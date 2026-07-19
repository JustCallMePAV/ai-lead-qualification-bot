from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.lead import LeadRecord
from app.schemas.lead import LeadCreate, QualificationResult


class DuplicateLeadError(Exception):
    pass


class LeadRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_external_id(self, external_id: str) -> LeadRecord | None:
        return self.session.scalar(select(LeadRecord).where(LeadRecord.external_id == external_id))

    def create(self, lead: LeadCreate, result: QualificationResult, warnings: list[str]) -> LeadRecord:
        record = LeadRecord(
            external_id=lead.external_id,
            name=lead.name,
            email=str(lead.email),
            company=lead.company,
            lead_data=lead.model_dump(mode="json"),
            result_data=result.model_dump(mode="json"),
            model_used=result.model_used,
            integration_warnings=warnings,
        )
        self.session.add(record)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise DuplicateLeadError from exc
        self.session.refresh(record)
        return record
