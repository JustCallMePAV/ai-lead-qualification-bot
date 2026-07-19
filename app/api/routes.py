from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_qualification_service
from app.schemas.lead import LeadCreate, QualificationResponse
from app.services.qualification import LeadQualificationService

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/v1/leads/qualify", response_model=QualificationResponse)
def qualify_lead(lead: LeadCreate, service: LeadQualificationService = Depends(get_qualification_service)):
    try:
        return service.qualify(lead)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Lead qualification is temporarily unavailable") from exc
