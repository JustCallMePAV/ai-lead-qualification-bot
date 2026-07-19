import json
from typing import Protocol

from openai import OpenAI

from app.prompts.qualification import SYSTEM_PROMPT
from app.schemas.lead import LeadCreate, QualificationResult


class QualificationClient(Protocol):
    def qualify(self, lead: LeadCreate) -> QualificationResult: ...


class OpenAIQualificationClient:
    def __init__(self, api_key: str, model: str, timeout: float, max_retries: int):
        self.model = model
        self.client = OpenAI(api_key=api_key, timeout=timeout, max_retries=max_retries)

    def qualify(self, lead: LeadCreate) -> QualificationResult:
        response = self.client.responses.parse(
            model=self.model,
            instructions=SYSTEM_PROMPT,
            input=json.dumps(lead.model_dump(mode="json"), ensure_ascii=False),
            text_format=QualificationResult,
        )
        if response.output_parsed is None:
            raise RuntimeError("The model did not return a qualification result")
        return response.output_parsed.model_copy(update={"model_used": self.model})
