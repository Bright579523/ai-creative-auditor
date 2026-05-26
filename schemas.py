"""Pydantic schemas for structured LLM audit outputs."""

from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    visual_hierarchy: int = Field(ge=1, le=10)
    color_psychology: int = Field(ge=1, le=10)
    message_clarity: int = Field(ge=1, le=10)
    audience_fit: int = Field(ge=1, le=10)


class CreativeAuditResult(BaseModel):
    corrected_text: str
    design_score: int = Field(ge=1, le=10)
    business_score: int = Field(ge=1, le=10)
    actionable_feedback: str
    score_breakdown: ScoreBreakdown
    campaign_type_guess: str | None = None

    def to_legacy_dict(self) -> dict:
        """Flat dict for Streamlit gauges and backward-compatible consumers."""
        data = self.model_dump()
        data["score_breakdown"] = self.score_breakdown.model_dump()
        return data
