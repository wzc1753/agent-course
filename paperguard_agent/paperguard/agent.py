"""
Core review agent logic using Claude API.
"""

import anthropic
from typing import Optional
from paperguard.config import Config
from paperguard.schemas import ReviewRequest, ReviewResult, ReviewSection
import json
import re


class ReviewAgent:
    """Agent for reviewing academic papers using Claude."""

    def __init__(self, config: Config):
        """Initialize the review agent."""
        self.config = config
        if not config.validate_api_key():
            raise ValueError("ANTHROPIC_API_KEY is not set or invalid")
        self.client = anthropic.Anthropic(api_key=config.anthropic_api_key)

    def _build_review_prompt(self, request: ReviewRequest) -> str:
        """Build the system prompt for paper review."""
        base_prompt = """You are an expert academic paper reviewer with deep knowledge across multiple fields.
Your task is to provide a thorough, constructive, and fair review of the submitted paper.

Review the paper carefully and provide:
1. A brief summary of the paper's contributions
2. Key strengths (3-5 points)
3. Key weaknesses (3-5 points)
4. Detailed feedback organized by sections
5. An overall assessment with score and recommendation

Be specific, cite line numbers or sections when possible, and maintain a professional tone.
Focus on: novelty, technical soundness, clarity, experimental validation, and related work coverage."""

        if request.focus_aspects and "all" not in [a.value for a in request.focus_aspects]:
            aspects = ", ".join([a.value for a in request.focus_aspects])
            base_prompt += f"\n\nPay special attention to: {aspects}"

        if request.additional_instructions:
            base_prompt += f"\n\nAdditional instructions: {request.additional_instructions}"

        return base_prompt

    def _parse_review_response(self, response_text: str) -> ReviewResult:
        """Parse Claude's response into structured ReviewResult."""
        # This is a simplified parser - in production, you might use structured output
        sections = []
        strengths = []
        weaknesses = []
        summary = ""
        recommendation = None
        score = None

        # Extract sections using regex patterns
        summary_match = re.search(r"(?:summary|overview):\s*(.+?)(?=\n\n|\nstrengths:|\Z)", response_text, re.IGNORECASE | re.DOTALL)
        if summary_match:
            summary = summary_match.group(1).strip()

        strengths_match = re.search(r"strengths?:\s*(.+?)(?=\n\nweaknesses?:|\Z)", response_text, re.IGNORECASE | re.DOTALL)
        if strengths_match:
            strength_text = strengths_match.group(1).strip()
            strengths = [s.strip("- •*").strip() for s in strength_text.split("\n") if s.strip()]

        weaknesses_match = re.search(r"weaknesses?:\s*(.+?)(?=\n\n|\Z)", response_text, re.IGNORECASE | re.DOTALL)
        if weaknesses_match:
            weakness_text = weaknesses_match.group(1).strip()
            weaknesses = [w.strip("- •*").strip() for w in weakness_text.split("\n") if w.strip()]

        score_match = re.search(r"(?:score|rating):\s*(\d+(?:\.\d+)?)", response_text, re.IGNORECASE)
        if score_match:
            score = float(score_match.group(1))

        recommendation_match = re.search(r"recommendation:\s*(\w+)", response_text, re.IGNORECASE)
        if recommendation_match:
            recommendation = recommendation_match.group(1)

        return ReviewResult(
            summary=summary or "Review completed",
            strengths=strengths,
            weaknesses=weaknesses,
            detailed_sections=sections,
            overall_score=score,
            recommendation=recommendation,
            review_metadata={"raw_response": response_text}
        )

    async def review_paper(self, request: ReviewRequest) -> ReviewResult:
        """Perform paper review using Claude API."""
        system_prompt = self._build_review_prompt(request)

        try:
            message = self.client.messages.create(
                model=self.config.model_name,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": f"Please review the following paper:\n\n{request.paper_content}"
                    }
                ]
            )

            response_text = message.content[0].text
            review_result = self._parse_review_response(response_text)

            return review_result

        except anthropic.APIError as e:
            raise Exception(f"API error during review: {str(e)}")
