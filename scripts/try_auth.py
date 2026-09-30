from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)
body = {"submission_id": 1, "submission_url": "x", "memo_url": "y",
        "total_points": 10}

print("health, no key      ->", client.get("/health").status_code, "(want 200)")
print("mark, no key        ->", client.post("/mark", json=body).status_code, "(want 401)")
print("mark, wrong key     ->", client.post("/mark", json=body,
      headers={"X-API-Key": "wrong"}).status_code, "(want 401)")
right = client.post("/mark", json=body,
                    headers={"X-API-Key": settings.service_api_key})
print("mark, right key     ->", right.status_code, "(want 502, key accepted,")
print("                       download of fake URL fails)")
