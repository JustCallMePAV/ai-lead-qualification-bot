import json
from pathlib import Path

import httpx

root = Path(__file__).resolve().parents[1]
for filename in ("high-priority.json", "medium-priority.json", "low-priority.json"):
    payload = json.loads((root / "examples" / filename).read_text(encoding="utf-8"))
    response = httpx.post("http://localhost:8000/api/v1/leads/qualify", json=payload, timeout=10)
    response.raise_for_status()
    body = response.json()
    print(
        f"{filename}: {body['result']['score']} / {body['result']['priority']} "
        f"(existing={body['existing']})"
    )
