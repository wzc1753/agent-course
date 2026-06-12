"""
Agent-based pipeline for PaperGuard.
This replaces the functional pipeline with a true multi-agent system.
"""
from typing import Optional, List
import logging

from .agents import SupervisorAgent
from .report import AuditReport
from .schemas import AuditIssue

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_audit_with_agents(
    paper_content: str,
    bib_content: Optional[str] = None,
    mode: str = "Standard",
    max_claims: int = 10
) -> AuditReport:
    """
    Run audit using multi-agent system.
    
    This is the agent-based version that uses:
    - SupervisorAgent to coordinate
    - ParserAgent to parse paper
    - CitationVerifierAgent to verify references
    - ClaimVerifierAgent to verify claims (Full mode)
    
    Args:
        paper_content: Full text of the paper
        bib_content: Optional BibTeX content
        mode: Audit mode - "Fast", "Standard", or "Full"
        max_claims: Maximum number of claims to verify
        
    Returns:
        AuditReport with all detected issues and agent traces
    """
    logger.info(f"🤖 Starting Multi-Agent Audit in {mode} mode")
    
    # Initialize supervisor agent
    supervisor = SupervisorAgent()
    
    # Run multi-agent workflow
    agent_input = {
        "paper_content": paper_content,
        "bib_content": bib_content,
        "mode": mode,
        "max_claims": max_claims
    }
    
    results = supervisor.run(agent_input)
    
    # Convert agent results to AuditIssues
    issues = []

    # Check citation-reference consistency
    parsed = results["parsed"]

    # Helper to get field from dict or object
    def get_field(obj, field, default=None):
        if hasattr(obj, field):
            return getattr(obj, field, default)
        elif isinstance(obj, dict):
            return obj.get(field, default)
        return default

    ref_ids = {get_field(ref, 'ref_id') for ref in parsed["references"] if get_field(ref, 'ref_id')}
    cited_ids = {rid for cit in parsed["citations"] for rid in get_field(cit, 'ref_ids', [])}

    # Missing references
    for cit in parsed["citations"]:
        cit_ref_ids = get_field(cit, 'ref_ids', [])
        for rid in cit_ref_ids:
            if rid not in ref_ids:
                issues.append(AuditIssue(
                    issue_id=f"agent-missing-{rid}",
                    issue_type="MISSING_REFERENCE",
                    severity="HIGH",
                    location=f"Citation {get_field(cit, 'raw_marker', '?')}",
                    original_text=get_field(cit, 'sentence', ''),
                    diagnosis=f"[Agent Detection] Citation [{rid}] missing from bibliography",
                    evidence=[f"Detected by: {supervisor.agent_id}", get_field(cit, 'sentence', '')],
                    recommendation=f"Add reference [{rid}] or remove citation",
                    verifier_trace=[{
                        "agent": "supervisor",
                        "step": "consistency_check",
                        "result": "missing_reference"
                    }]
                ))
    
    # Unused references
    for ref in parsed["references"]:
        ref_id = get_field(ref, 'ref_id')
        if ref_id and ref_id not in cited_ids:
            raw_text = get_field(ref, 'raw_text', '')
            issues.append(AuditIssue(
                issue_id=f"agent-unused-{ref_id}",
                issue_type="UNUSED_REFERENCE",
                severity="LOW",
                location=f"Reference {ref_id}",
                original_text=raw_text[:100] if raw_text else '',
                diagnosis=f"[Agent Detection] Reference not cited in text",
                evidence=[f"Detected by: {supervisor.agent_id}"],
                recommendation="Remove or cite this reference",
                verifier_trace=[{
                    "agent": "supervisor",
                    "step": "consistency_check",
                    "result": "unused_reference"
                }]
            ))
    
    # Add verification results
    if "citation_verification" in results:
        for v in results["citation_verification"]:
            if v["status"] in ["NOT_FOUND", "METADATA_MISMATCH"]:
                issues.append(AuditIssue(
                    issue_id=f"agent-verify-{v['ref_id']}",
                    issue_type=v["status"],
                    severity="HIGH" if v["status"] == "NOT_FOUND" else "MEDIUM",
                    location=f"Reference {v['ref_id']}",
                    original_text=f"Reference {v['ref_id']}",
                    diagnosis=f"[Agent Verification] {v['status']}",
                    evidence=v.get("evidence", []) + [f"Verified by: citation_verifier"],
                    recommendation="Verify reference details or provide correct metadata",
                    verifier_trace=[{
                        "agent": "citation_verifier",
                        "confidence": v["confidence"],
                        "status": v["status"]
                    }]
                ))
    
    # Create audit report with agent traces
    report = AuditReport(issues=issues)
    report.agent_traces = results.get("agent_traces", [])
    
    logger.info(f"🤖 Multi-Agent Audit complete: {len(issues)} issues found")
    logger.info(f"📊 Agent traces: {len(report.agent_traces)} agents participated")
    
    return report
