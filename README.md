# AI Lead Qualification Bot

A portfolio-ready FastAPI service that validates inbound B2B leads, qualifies them with structured OpenAI output, stores idempotent results, and optionally synchronizes Airtable and notifies Slack. Its deterministic demo mode runs entirely offline.

## Business use case and features

Sales teams can turn unstructured enquiries into consistent scores, priorities, summaries, actions, follow-up questions, and draft replies. The MVP includes Pydantic validation, SQLAlchemy persistence, duplicate suppression by `external_id`, graceful optional integrations, configurable CORS/timeouts/retries, three sample leads, tests, Docker, CI, and optional n8n automation.

## Architecture

```mermaid
flowchart LR
    Lead --> API[FastAPI webhook]
    API --> Service[Qualification service]
    Service --> DB[(SQLite / PostgreSQL)]
    Service --> Engine{Demo rules or OpenAI Responses API}
    Service -. optional .-> Airtable
    Service -. medium/high .-> Slack
```

Business logic stays in `app/services`; integrations and repositories are injected and mockable. See [architecture](docs/architecture.md) and the [scoring rubric](docs/scoring-rubric.md).

## Stack and structure

Python 3.12, FastAPI, Pydantic 2, OpenAI Python SDK with Responses API structured output, SQLAlchemy 2, SQLite, HTTPX, pytest, Ruff, Docker Compose, and GitHub Actions.

```text
app/             API, configuration, schemas, service, adapters, repository, prompt
tests/           API/service tests with mocked external systems
examples/        High-, medium-, and low-priority JSON requests
scripts/demo.py  Three-lead demonstration
docs/            Architecture and scoring details
n8n/             Optional importable workflow
```

## Local installation and demo mode

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

On macOS/Linux, activate with `source .venv/bin/activate` and copy with `cp .env.example .env`.

`DEMO_MODE=true` is the safe default: no OpenAI, Airtable, or Slack request occurs. Results have `demo_generated: true`, `model_used: demo-rules-v1`, and a `demo-generated` tag; simulated operations are logged. Open <http://localhost:8000/docs> or run `python scripts/demo.py` in another terminal.

## API

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/leads/qualify \
  -H "Content-Type: application/json" \
  --data @examples/high-priority.json
```

Abbreviated response:

```json
{
  "external_id": "lead-demo-high",
  "existing": false,
  "demo_generated": true,
  "result": {
    "category": "AI automation opportunity",
    "score": 90,
    "priority": "high",
    "model_used": "demo-rules-v1",
    "qualified_at": "2026-07-19T12:00:00Z"
  },
  "integration_warnings": []
}
```

The actual result also includes intent, fit, summary, reasoning, action, owner, questions, response draft, and tags. Submit the same `external_id` again and `existing` becomes `true` without repeating qualification or integrations.

## Live configuration

Copy `.env.example` to `.env`; it is Git-ignored. Set `DEMO_MODE=false` and `OPENAI_API_KEY`. `OPENAI_MODEL` defaults to `gpt-5.6-luna`, the current cost-sensitive model chosen for structured classification, and is configurable. Live code uses `client.responses.parse(..., text_format=QualificationResult)`.

### Airtable

Set `AIRTABLE_API_TOKEN`, `AIRTABLE_BASE_ID`, and `AIRTABLE_TABLE_NAME`. Create columns named External ID, Name, Email, Company, Message, Source, Score (number), Priority, Summary, Recommended Action, Tags, and Qualified At. Partial configuration disables Airtable. Failures become warnings and logs never include credentials.

### Slack

Create an Incoming Webhook and set `SLACK_WEBHOOK_URL`. `SLACK_MIN_PRIORITY=medium` sends medium/high leads; choose `low` or `high` if needed. Slack is optional and failures do not discard results.

PostgreSQL can later use a URL such as `postgresql+psycopg://user:password@host/db` after adding Psycopg.

## Docker and tests

```bash
docker compose up --build
docker compose config
docker compose down

pytest
ruff check .
```

Compose persists SQLite in a named volume and defaults to demo mode. Tests cover health, validation, schema enforcement, all priorities, duplicate side effects, qualifier failure, Airtable/Slack failures, disabled integrations, demo behavior, and a no-external-HTTP guard.

## n8n

Import `n8n/lead-qualification-workflow.json`. Change the HTTP Request URL when n8n cannot resolve `host.docker.internal:8000`, activate the workflow, and POST a lead to its webhook. The API never depends on n8n.

## Security, reliability, and limitations

Secrets are environment-only; logs use only `external_id`; outbound requests have timeouts and retries; CORS is allow-listed; clients receive safe upstream errors. Because original lead data is retained for audit/demo purposes, add retention, encryption, and access controls before production.

This synchronous MVP creates tables at startup and cannot guarantee exactly-once external side effects for two truly simultaneous first submissions. The best next improvement is transactional idempotency reservation plus an outbox worker. Production should also add Alembic, authentication/rate limits, PostgreSQL, encrypted PII retention, metrics/tracing, and integration circuit breakers.

## License

MIT
