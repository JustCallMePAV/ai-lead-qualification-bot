from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.integrations.airtable import AirtableClient, DemoAirtableClient
from app.integrations.demo_client import DemoQualificationClient
from app.integrations.openai_client import OpenAIQualificationClient
from app.integrations.slack import DemoSlackClient, SlackClient
from app.repositories.leads import LeadRepository
from app.services.qualification import LeadQualificationService


def get_qualification_service(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    if settings.demo_mode:
        qualifier, airtable, slack = DemoQualificationClient(), DemoAirtableClient(), DemoSlackClient()
    else:
        qualifier = OpenAIQualificationClient(
            settings.openai_api_key or "",
            settings.openai_model,
            settings.request_timeout_seconds,
            settings.max_retries,
        )
        airtable = (
            AirtableClient(
                settings.airtable_api_token or "", settings.airtable_base_id or "",
                settings.airtable_table_name or "", settings.request_timeout_seconds, settings.max_retries,
            ) if settings.airtable_enabled else None
        )
        slack = (
            SlackClient(settings.slack_webhook_url, settings.request_timeout_seconds, settings.max_retries)
            if settings.slack_webhook_url
            else None
        )
    return LeadQualificationService(
        LeadRepository(db), qualifier, airtable, slack, settings.demo_mode, settings.slack_min_priority
    )
