import logging
from urllib.parse import quote

from app.integrations.http import post_with_retry
from app.schemas.lead import LeadCreate, QualificationResult

logger = logging.getLogger(__name__)


class AirtableClient:
    def __init__(self, token: str, base_id: str, table_name: str, timeout: float, max_retries: int = 2):
        self.url = f"https://api.airtable.com/v0/{quote(base_id, safe='')}/{quote(table_name, safe='')}"
        self.headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        self.timeout = timeout
        self.max_retries = max_retries

    def create_record(self, lead: LeadCreate, result: QualificationResult) -> None:
        fields = {"External ID": lead.external_id, "Name": lead.name, "Email": str(lead.email),
                  "Company": lead.company or "", "Message": lead.message, "Source": lead.source or "",
                  "Score": result.score, "Priority": result.priority.value, "Summary": result.summary,
                  "Recommended Action": result.recommended_action, "Tags": ", ".join(result.tags),
                  "Qualified At": result.qualified_at.isoformat()}
        post_with_retry(
            self.url,
            headers=self.headers,
            json={"fields": fields},
            timeout=self.timeout,
            max_retries=self.max_retries,
        )


class DemoAirtableClient:
    def create_record(self, lead: LeadCreate, result: QualificationResult) -> None:
        logger.info("Demo mode: simulated Airtable save for external_id=%s", lead.external_id)
