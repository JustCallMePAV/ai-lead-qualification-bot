from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from app.api.dependencies import get_qualification_service
from app.integrations.demo_client import DemoQualificationClient
from app.integrations.http import post_with_retry
from app.main import app
from app.repositories.leads import LeadRepository
from app.schemas.lead import LeadCreate, QualificationResult
from app.services.qualification import LeadQualificationService


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


@pytest.mark.parametrize("kind,expected", [("high", "high"), ("medium", "medium"), ("low", "low")])
def test_demo_priority_outcomes(client, payloads, kind, expected):
    body = client.post("/api/v1/leads/qualify", json=payloads[kind]).json()
    assert body["result"]["priority"] == expected
    assert body["demo_generated"] is True
    QualificationResult.model_validate(body["result"])


def test_invalid_request_returns_useful_422(client, payloads):
    response = client.post("/api/v1/leads/qualify", json=payloads["high"] | {"email": "bad"})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == "email"


def test_structured_result_rejects_invalid_score():
    with pytest.raises(ValidationError):
        QualificationResult.model_validate({"score": 101})


def test_duplicate_does_not_repeat_side_effects(session, payloads):
    qualifier, airtable, slack = Mock(wraps=DemoQualificationClient()), Mock(), Mock()
    service = LeadQualificationService(LeadRepository(session), qualifier, airtable, slack, True, "low")
    lead = LeadCreate.model_validate(payloads["high"])
    first, second = service.qualify(lead), service.qualify(lead)
    assert first.existing is False and second.existing is True
    qualifier.qualify.assert_called_once()
    airtable.create_record.assert_called_once()
    slack.notify.assert_called_once()


def test_qualifier_failure_is_safe_503(client, payloads, session):
    qualifier = Mock()
    qualifier.qualify.side_effect = RuntimeError("secret upstream detail")
    app.dependency_overrides[get_qualification_service] = lambda: LeadQualificationService(
        LeadRepository(session), qualifier
    )
    response = client.post("/api/v1/leads/qualify", json=payloads["high"])
    assert response.status_code == 503
    assert response.json() == {"detail": "Lead qualification is temporarily unavailable"}


@pytest.mark.parametrize(
    "integration,warning",
    [("airtable", "Airtable synchronization failed"), ("slack", "Slack notification failed")],
)
def test_optional_integration_failure_is_non_fatal(session, payloads, integration, warning):
    broken = Mock()
    method = "create_record" if integration == "airtable" else "notify"
    getattr(broken, method).side_effect = RuntimeError("down")
    service = LeadQualificationService(
        LeadRepository(session), DemoQualificationClient(), slack_min_priority="low", **{integration: broken}
    )
    result = service.qualify(LeadCreate.model_validate(payloads["high"]))
    assert warning in result.integration_warnings


def test_runs_without_optional_integrations(session, payloads):
    service = LeadQualificationService(LeadRepository(session), DemoQualificationClient())
    assert service.qualify(LeadCreate.model_validate(payloads["medium"])).result.priority.value == "medium"


def test_low_priority_skips_default_slack(session, payloads):
    slack = Mock()
    service = LeadQualificationService(LeadRepository(session), DemoQualificationClient(), slack=slack)
    service.qualify(LeadCreate.model_validate(payloads["low"]))
    slack.notify.assert_not_called()


def test_no_external_network_calls(client, payloads, monkeypatch):
    import httpx

    monkeypatch.setattr(httpx, "post", Mock(side_effect=AssertionError("external network disabled")))
    response = client.post(
        "/api/v1/leads/qualify", json=payloads["high"] | {"external_id": "offline-test"}
    )
    assert response.status_code == 200


def test_transient_http_failure_is_retried(monkeypatch):
    import httpx

    request = httpx.Request("POST", "https://example.invalid")
    responses = [httpx.Response(503, request=request), httpx.Response(200, request=request)]
    post = Mock(side_effect=responses)
    sleep = Mock()
    monkeypatch.setattr(httpx, "post", post)
    response = post_with_retry(
        "https://example.invalid", json={}, timeout=1, max_retries=2, sleep=sleep
    )
    assert response.status_code == 200
    assert post.call_count == 2
    sleep.assert_called_once_with(0.25)
