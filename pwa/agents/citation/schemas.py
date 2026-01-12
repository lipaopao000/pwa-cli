from typing import List, Optional

from pydantic import BaseModel, Field


class LocalSupportEvaluation(BaseModel):
    """Evaluation of whether a specific paper supports a claim."""

    local_support: str = Field(
        description="Support level: 'Full', 'Partial', 'Not Mentioned', 'Contradictory'"
    )
    reasoning: str = Field(
        description="Detailed explanation of the support level based on evidence."
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score for this evaluation.")


class GlobalFactualityEvaluation(BaseModel):
    """Evaluation of the general truthfulness of a claim."""

    factuality: str = Field(
        description="Factuality label: 'Well-established', 'Supported by Evidence', 'Debatable', 'Unsupported', 'Contradicted', 'Requires Specification'"
    )
    reasoning: str = Field(description="Synthesis of all evidence and conclusion.")
    suggested_key: Optional[str] = Field(
        default=None, description="Optional better citation key or URL."
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score for this evaluation.")


class SearchQuery(BaseModel):
    """A generated search query for verification."""

    query: str = Field(description="The search query string.")
