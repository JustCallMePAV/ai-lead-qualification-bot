import logging

from app.integrations.http import post_with_retry
from app.schemas.lead import LeadCreate, QualificationResult

logger = logging.getLogger(__name__)


class SlackClient:
    def __init__(self, webhook_url: str, timeout: float, max_retries: int = 2):
        self.webhook_url = webhook_url
        self.timeout = timeout
        self.max_retries = max_retries

    def notify(self, lead: LeadCreate, result: QualificationResult) -> None:
        company = f" at {lead.company}" if lead.company else ""
        text = (f"New {result.priority.value}-priority lead: {lead.name}{company}\n"
                f"Score: {result.score}/100\n{result.summary}\nNext: {result.recommended_action}")
        post_with_retry(
            self.webhook_url,
            json={"text": text},
            timeout=self.timeout,
            max_retries=self.max_retries,
        )


class DemoSlackClient:
    def notify(self, lead: LeadCreate, result: QualificationResult) -> None:
        logger.info("Demo mode: simulated Slack notification for external_id=%s", lead.external_id)
