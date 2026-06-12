"""Claim-citation support verification using LLM."""
import os
import json
from typing import Optional
from .schemas import ClaimVerificationResult, ReferenceEntry

# Support both OpenAI and MiniMax
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def verify_claim(
    claim_text: str,
    reference: ReferenceEntry,
    abstract: Optional[str] = None
) -> ClaimVerificationResult:
    """
    Verify if citation supports the claim using LLM.
    
    Supports:
    - MiniMax-M3 (preferred if MINIMAX_API_KEY is set)
    - OpenAI GPT-4 (fallback)
    - Simple keyword-based (if no API available)
    
    Args:
        claim_text: The claim sentence from the paper
        reference: The cited reference metadata
        abstract: Optional abstract of the cited paper
        
    Returns:
        ClaimVerificationResult with verdict and suggestions
    """
    # Check for MiniMax API key first
    minimax_key = os.getenv("MINIMAX_API_KEY")
    minimax_group_id = os.getenv("MINIMAX_GROUP_ID")
    
    if minimax_key and minimax_group_id:
        return _verify_with_minimax(claim_text, reference, abstract, minimax_key, minimax_group_id)
    
    # Fallback to OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and OPENAI_AVAILABLE:
        return _verify_with_openai(claim_text, reference, abstract, openai_key)
    
    # Final fallback: keyword-based
    return _fallback_verification(claim_text, reference)


def _verify_with_minimax(
    claim_text: str,
    reference: ReferenceEntry,
    abstract: Optional[str],
    api_key: str,
    group_id: str
) -> ClaimVerificationResult:
    """Verify using MiniMax-M3 model."""
    try:
        import requests
        
        prompt = f"""你是一个学术论文审查专家，负责验证引用是否支持论断。

任务：判断被引用的论文是否支持手稿中的论断。

论断: "{claim_text}"

引用文献信息:
- 标题: {reference.title or '未知'}
- 作者: {', '.join(reference.authors) if reference.authors else '未知'}
- 年份: {reference.year or '未知'}
- 期刊/会议: {reference.venue or '未知'}
- 摘要: {abstract or '不可用'}

请以JSON格式返回，包含以下字段：
{{
  "verdict": "SUPPORTED | PARTIALLY_SUPPORTED | UNSUPPORTED | NOT_ENOUGH_INFO",
  "severity": "LOW | MEDIUM | HIGH",
  "reason": "...",
  "suggested_revision": "..."
}}

规则:
- 不要仅凭关键词重合就判断支持
- 如果论断的范围比证据更广，使用PARTIALLY_SUPPORTED
- 如果只有标题/摘要且信息不足，使用NOT_ENOUGH_INFO
- 不要编造新引用
- 修改建议必须比原论断更保守
"""
        
        url = f"https://api.minimax.chat/v1/text/chatcompletion_v2"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "abab6.5s-chat",  # MiniMax-M3
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个学术论文审查专家。只返回有效的JSON。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.01,
            "top_p": 0.95,
            "reply_constraints": {
                "sender_type": "BOT",
                "sender_name": "PaperGuard"
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result_data = response.json()
        content = result_data["choices"][0]["message"]["content"]
        
        # Parse JSON from response
        result = json.loads(content)
        
        return ClaimVerificationResult(
            mention_id="",
            claim=claim_text,
            cited_ref_ids=[reference.ref_id],
            verdict=result.get("verdict", "NOT_ENOUGH_INFO"),
            severity=result.get("severity", "MEDIUM"),
            reason=result.get("reason", "MiniMax-M3 verification completed"),
            evidence_used=[f"Title: {reference.title}", "Verified by: MiniMax-M3"],
            suggested_revision=result.get("suggested_revision")
        )
        
    except Exception as e:
        print(f"MiniMax verification failed: {e}")
        return _fallback_verification(claim_text, reference)


def _verify_with_openai(
    claim_text: str,
    reference: ReferenceEntry,
    abstract: Optional[str],
    api_key: str
) -> ClaimVerificationResult:
    """Verify using OpenAI GPT-4."""
    try:
        client = OpenAI(api_key=api_key)
        
        prompt = f"""You are a scholarly claim-citation verifier.

Task: Determine whether the cited paper supports the claim made in the manuscript.

Claim: "{claim_text}"

Citation metadata:
- Title: {reference.title or 'Unknown'}
- Authors: {', '.join(reference.authors) if reference.authors else 'Unknown'}
- Year: {reference.year or 'Unknown'}
- Venue: {reference.venue or 'Unknown'}
- Abstract: {abstract or 'Not available'}

Return JSON only with these fields:
{{
  "verdict": "SUPPORTED | PARTIALLY_SUPPORTED | UNSUPPORTED | NOT_ENOUGH_INFO",
  "severity": "LOW | MEDIUM | HIGH",
  "reason": "...",
  "suggested_revision": "..."
}}

Rules:
- Do not assume support from keyword overlap alone
- If claim is broader than evidence, use PARTIALLY_SUPPORTED
- If only title/abstract available and insufficient, use NOT_ENOUGH_INFO
- Do not invent new citations
- Suggested revision must be more conservative
"""
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a scholarly claim verifier. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return ClaimVerificationResult(
            mention_id="",
            claim=claim_text,
            cited_ref_ids=[reference.ref_id],
            verdict=result.get("verdict", "NOT_ENOUGH_INFO"),
            severity=result.get("severity", "MEDIUM"),
            reason=result.get("reason", "OpenAI GPT-4 verification completed"),
            evidence_used=[f"Title: {reference.title}", "Verified by: GPT-4"],
            suggested_revision=result.get("suggested_revision")
        )
        
    except Exception as e:
        print(f"OpenAI verification failed: {e}")
        return _fallback_verification(claim_text, reference)


def _fallback_verification(claim_text: str, reference: ReferenceEntry) -> ClaimVerificationResult:
    """Simple keyword-based fallback verification."""
    
    # Check for overstrong claims
    strong_words = ['first', 'solve', 'prove', 'all', 'always', 'never', 'completely', 'guarantee']
    has_strong = any(word in claim_text.lower() for word in strong_words)
    
    if has_strong:
        verdict = "PARTIALLY_SUPPORTED"
        severity = "MEDIUM"
        reason = "Claim contains strong language that may not be fully supported"
        suggestion = claim_text.replace("first", "among the first").replace(
            "solve", "address").replace("all", "many").replace(
            "completely", "largely")
    else:
        verdict = "NOT_ENOUGH_INFO"
        severity = "LOW"
        reason = "Unable to verify without LLM API"
        suggestion = None
    
    return ClaimVerificationResult(
        mention_id="",
        claim=claim_text,
        cited_ref_ids=[reference.ref_id],
        verdict=verdict,
        severity=severity,
        reason=reason,
        evidence_used=["Fallback verification used"],
        suggested_revision=suggestion
    )
