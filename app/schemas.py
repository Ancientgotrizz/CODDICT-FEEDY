"""
schemas.py
----------
Defines the exact shape the AI's answer must fit into. This is the
contract between the AI model and the rest of the app: if the model's
reply doesn't match this shape, it gets rejected instead of silently
breaking something downstream.
"""

from typing import Literal
from pydantic import BaseModel, Field

# The four categories - exactly these four, nothing else is allowed.
SatisfactionCategory = Literal["Excellent", "Good", "Need Improvements", "Poor"]


class FeedbackClassification(BaseModel):
    """The strict, validated shape of one classification result."""

    category: SatisfactionCategory = Field(
        description="Exactly one of: Excellent, Good, Need Improvements, Poor"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="The model's own honest confidence in this classification, from 0 to 1",
    )
    rationale: str = Field(
        description="One or two plain-language sentences explaining the decision, "
        "referring to what the customer actually wrote"
    )
    flagged_keywords: list[str] = Field(
        default_factory=list,
        description="Important words or short phrases copied from the actual customer "
        "feedback that support the rationale; explanatory only, must not decide the category",
    )
