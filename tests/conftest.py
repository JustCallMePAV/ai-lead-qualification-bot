import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_qualification_service
from app.core.database import Base
from app.integrations.demo_client import DemoQualificationClient
from app.main import app
from app.repositories.leads import LeadRepository
from app.services.qualification import LeadQualificationService


@pytest.fixture
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as value:
        yield value


@pytest.fixture
def service(session):
    return LeadQualificationService(LeadRepository(session), DemoQualificationClient(), demo_mode=True)


@pytest.fixture
def client(service):
    app.dependency_overrides[get_qualification_service] = lambda: service
    with TestClient(app) as value:
        yield value
    app.dependency_overrides.clear()


@pytest.fixture
def payloads():
    root = Path(__file__).resolve().parents[1] / "examples"
    return {name: json.loads((root / f"{name}-priority.json").read_text(encoding="utf-8"))
            for name in ("high", "medium", "low")}
