import logging

from app.repositories.leads import DuplicateLeadError, LeadRepository
from app.schemas.lead import LeadCreate, Priority, QualificationResponse, QualificationResult

logger = logging.getLogger(__name__)


class LeadQualificationService:
    def __init__(self, repository: LeadRepository, qualifier, airtable=None, slack=None,
                 demo_mode: bool = False, slack_min_priority: str = "medium"):
        self.repository, self.qualifier = repository, qualifier
        self.airtable, self.slack = airtable, slack
        self.demo_mode, self.slack_min_priority = demo_mode, slack_min_priority

    def qualify(self, lead: LeadCreate) -> QualificationResponse:
        existing = self.repository.get_by_external_id(lead.external_id)
        if existing:
            return self._response(existing, True)
        result = self.qualifier.qualify(lead)
        warnings: list[str] = []
        if self.airtable:
            try:
                self.airtable.create_record(lead, result)
            except Exception:
                logger.exception("Airtable operation failed for external_id=%s", lead.external_id)
                warnings.append("Airtable synchronization failed")
        if self.slack and self._should_notify(result.priority):
            try:
                self.slack.notify(lead, result)
            except Exception:
                logger.exception("Slack operation failed for external_id=%s", lead.external_id)
                warnings.append("Slack notification failed")
        try:
            record = self.repository.create(lead, result, warnings)
        except DuplicateLeadError:
            record = self.repository.get_by_external_id(lead.external_id)
            if record is None:
                raise
            return self._response(record, True)
        return self._response(record, False)

    def _should_notify(self, priority: Priority) -> bool:
        rank = {"low": 0, "medium": 1, "high": 2}
        return rank[priority.value] >= rank[self.slack_min_priority]

    @staticmethod
    def _response(record, existing: bool) -> QualificationResponse:
        result = QualificationResult.model_validate(record.result_data)
        return QualificationResponse(external_id=record.external_id, existing=existing,
                                     demo_generated=result.model_used.startswith("demo-"), result=result,
                                     integration_warnings=record.integration_warnings or [])
