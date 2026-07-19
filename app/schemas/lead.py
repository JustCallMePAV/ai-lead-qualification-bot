from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class LeadCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    external_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    company: str | None = Field(default=None, max_length=200)
    job_title: str | None = Field(default=None, max_length=200)
    message: str = Field(min_length=10, max_length=5000)
    source: str | None = Field(default=None, max_length=100)
    budget: str | None = Field(default=None, max_length=100)
    timeline: str | None = Field(default=None, max_length=100)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def limit_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        if len(value) > 20:
            raise ValueError("metadata may contain at most 20 entries")
        return value


class QualificationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str = Field(min_length=1, max_length=100)
    score: int = Field(ge=0, le=100)
    priority: Priority
    intent: str = Field(min_length=1)
    estimated_fit: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    reasoning: str = Field(min_length=1)
    recommended_action: str = Field(min_length=1)
    suggested_owner: str = Field(min_length=1)
    follow_up_questions: list[str] = Field(default_factory=list, max_length=8)
    draft_response: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list, max_length=12)
    model_used: str = Field(min_length=1)
    qualified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class QualificationResponse(BaseModel):
    external_id: str
    existing: bool
    demo_generated: bool
    result: QualificationResult
    integration_warnings: list[str] = Field(default_factory=list)
