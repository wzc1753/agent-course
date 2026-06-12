"""
Concrete agent implementations for PaperGuard system.
"""
from typing import Dict, Any, List
import logging

from .base_agent import BaseAgent
from .schemas import ReferenceEntry, CitationMention
from .parser import split_paper
from .citation_extractor import extract_citations
from .reference_parser import parse_references, parse_bibtex
from .metadata_clients import search_all_sources
from .matcher import compute_match_score, classify_status
from .claim_extractor import extract_claims
from .claim_verifier import verify_claim

logger = logging.getLogger(__name__)


class ParserAgent(BaseAgent):
    """Agent responsible for parsing paper structure."""
    
    def __init__(self):
        super().__init__(agent_id="parser_agent", role="Paper Structure Parser")
    
    def reason(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """Decide parsing strategy based on input format."""
        # Debug: log what we received
        logger.debug(f"[ParserAgent] observation keys: {observation.keys()}")

        # BaseAgent.perceive wraps input in {"raw": ..., ...}
        raw_data = observation.get("raw", {})
        logger.debug(f"[ParserAgent] raw_data type: {type(raw_data)}")

        # Extract paper_content - try multiple paths
        paper_content = None
        bib_content = None

        if isinstance(raw_data, dict):
            # Try direct access
            paper_content = raw_data.get("paper_content")
            bib_content = raw_data.get("bib_content")

            # If still None, raw_data might be the observation itself
            if not paper_content and "paper_content" in observation:
                paper_content = observation.get("paper_content")
                bib_content = observation.get("bib_content")
        elif isinstance(raw_data, str):
            # If raw_data is already the paper content string
            paper_content = raw_data

        # Final fallback: empty string
        if not paper_content:
            paper_content = ""
            logger.warning("[ParserAgent] No paper_content found in observation!")
            logger.warning(f"[ParserAgent] observation structure: {list(observation.keys())}")
            if isinstance(raw_data, dict):
                logger.warning(f"[ParserAgent] raw_data structure: {list(raw_data.keys())}")

        has_latex = "\\cite" in str(paper_content) or "\\begin{document}" in str(paper_content)
        has_bib = bib_content is not None

        decision = {
            "strategy": "latex" if has_latex else "markdown",
            "use_bibtex": has_bib,
            "content": paper_content,
            "bib": bib_content
        }

        logger.info(f"[ParserAgent] Strategy: {decision['strategy']}, content_length: {len(paper_content)}")
        return decision
    
    def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Parse paper into structured components."""
        content = decision.get("content", "")

        # Ensure content is not None
        if not content:
            raise ValueError("No paper content provided to ParserAgent")

        body, refs = split_paper(content)
        citations = extract_citations(body)

        if decision.get("use_bibtex") and decision.get("bib"):
            references = parse_bibtex(decision["bib"])
        else:
            references = parse_references(refs)
        
        result = {
            "body": body,
            "references_section": refs,
            "citations": citations,
            "references": references,
            "stats": {
                "citations_count": len(citations),
                "references_count": len(references)
            }
        }
        
        logger.info(f"[ParserAgent] Parsed: {result['stats']}")
        return result


class CitationVerifierAgent(BaseAgent):
    """Agent responsible for verifying citation authenticity."""
    
    def __init__(self):
        super().__init__(agent_id="citation_verifier", role="Citation Authenticity Verifier")
        self.verified_cache = {}
    
    def reason(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """Decide which references to verify."""
        # Extract references from the wrapped observation
        raw_data = observation.get("raw", {})
        references = raw_data.get("references", [])
        
        priority_refs = []
        for ref in references:
            priority = 0
            if ref.doi:
                priority += 3
            if ref.year and ref.year >= 2020:
                priority += 2
            if ref.title:
                priority += 1
            
            priority_refs.append((priority, ref))
        
        priority_refs.sort(reverse=True, key=lambda x: x[0])
        
        decision = {
            "references_to_verify": [r for _, r in priority_refs[:10]],
            "strategy": "parallel_search"
        }
        
        logger.info(f"[CitationVerifier] Will verify {len(decision['references_to_verify'])} refs")
        return decision
    
    def act(self, decision: Dict[str, Any]) -> List[Dict]:
        """Verify references against external databases."""
        results = []

        for ref in decision["references_to_verify"]:
            # Ensure ref is a ReferenceEntry object
            if not isinstance(ref, ReferenceEntry):
                logger.warning(f"[CitationVerifier] Invalid reference type: {type(ref)}")
                continue

            # Check cache
            cache_key = getattr(ref, 'ref_id', None)
            if not cache_key:
                logger.warning(f"[CitationVerifier] Reference missing ref_id: {ref}")
                continue

            if cache_key in self.verified_cache:
                results.append(self.verified_cache[cache_key])
                continue

            if not ref.title:
                results.append({
                    "ref_id": cache_key,
                    "status": "MISSING_METADATA",
                    "confidence": 0.0
                })
                continue

            candidates = search_all_sources(ref.title, ref.authors, ref.year)

            if not candidates:
                result = {
                    "ref_id": cache_key,
                    "status": "NOT_FOUND",
                    "confidence": 0.0,
                    "evidence": ["No matches in external databases"]
                }
            else:
                best = candidates[0]
                score = compute_match_score(ref, best)
                status = classify_status(score)

                result = {
                    "ref_id": cache_key,
                    "status": status,
                    "confidence": score,
                    "best_match": {
                        "title": best.title,
                        "authors": best.authors,
                        "year": best.year
                    },
                    "evidence": [f"Matched with confidence {score:.2f}"]
                }

            self.verified_cache[cache_key] = result
            results.append(result)

        logger.info(f"[CitationVerifier] Verified {len(results)} references")
        return results


class SupervisorAgent(BaseAgent):
    """Supervisor agent coordinating the multi-agent system."""
    
    def __init__(self):
        super().__init__(agent_id="supervisor", role="System Supervisor")
        self.sub_agents = {
            "parser": ParserAgent(),
            "citation_verifier": CitationVerifierAgent()
        }
    
    def reason(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate multi-agent workflow."""
        # Extract data from observation
        raw_data = observation.get("raw", {})

        mode = raw_data.get("mode", "Standard")
        paper_content = raw_data.get("paper_content", "")
        bib_content = raw_data.get("bib_content")
        max_claims = raw_data.get("max_claims", 10)

        workflow = {
            "steps": ["parse", "verify_citations"],
            "mode": mode,
            "paper_content": paper_content,  # Pass through to act
            "bib_content": bib_content,      # Pass through to act
            "max_claims": max_claims
        }

        logger.info(f"[Supervisor] Workflow: {mode} mode, paper_length: {len(paper_content)}")
        return workflow
    
    def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Execute multi-agent workflow."""
        results = {"issues": [], "agent_traces": []}
        
        parser = self.sub_agents["parser"]
        parsed = parser.run({
            "paper_content": decision.get("paper_content"),
            "bib_content": decision.get("bib_content")
        })
        
        results["parsed"] = parsed
        results["agent_traces"].append(parser.get_trace())
        
        if decision["mode"] in ["Standard", "Full"]:
            verifier = self.sub_agents["citation_verifier"]
            verification = verifier.run({"references": parsed["references"]})
            
            results["citation_verification"] = verification
            results["agent_traces"].append(verifier.get_trace())
        
        logger.info(f"[Supervisor] Completed workflow")
        return results
