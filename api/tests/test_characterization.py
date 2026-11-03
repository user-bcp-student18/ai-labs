import base64
import sqlite3
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest
import urllib3
from fastapi.testclient import TestClient

from app.main import create_app

TEST_SECRET = "WORKSHOP_SECRET_2026"
ONE_HOUR_SECONDS = 3600
TASK_KEYS = {"id", "title", "description", "status", "owner", "priority", "createdAt"}
SUMMARY_KEYS = {"owner", "total", "byStatus", "highPriorityOpen"}
UPLOAD_KEYS = {"owner", "fileName", "storedAt", "size"}
HEALTH_KEYS = {"requestedBy", "status", "body"}


def auth_headers(username: str = "student", role: str = "STUDENT") -> dict[str, str]:
    raw = f"{username}|{role}|{int(time.time()) + ONE_HOUR_SECONDS}|{TEST_SECRET}"
    return {"Authorization": "Bearer " + base64.b64encode(raw.encode()).decode()}


@pytest.fixture
def make_app(tmp_path: Path) -> Callable[[], object]:
    def factory() -> object:
        return create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))

    return factory


def fake_health_response(status: int = 200, body: bytes = b'{"status":"UP"}') -> SimpleNamespace:
    return SimpleNamespace(status=status, data=body)


# H-API-05: forma de cada ruta
def test_h_api_05_routes_status_and_json_shapes(make_app, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(urllib3.PoolManager, "request", lambda *args, **kwargs: fake_health_response())
    with TestClient(make_app()) as client:
        listed = client.get("/api/tasks", headers=auth_headers())
        created = client.post("/api/tasks", headers=auth_headers(), json={"title": "Nueva"})
        summary = client.get("/api/summary", headers=auth_headers())
        uploaded = client.post(
            "/api/requirements",
            headers=auth_headers(),
            files={"file": ("req.txt", b"contenido", "text/plain")},
        )
        health = client.get("/api/backend-health", headers=auth_headers())

    assert listed.status_code == 200
    assert [task["id"] for task in listed.json()] == sorted(task["id"] for task in listed.json())
    assert len(listed.json()) == 2
    assert all(set(task) == TASK_KEYS for task in listed.json())
    assert created.status_code == 201
    assert set(created.json()) == TASK_KEYS
    assert (created.json()["status"], created.json()["priority"], created.json()["owner"]) == ("TODO", "MEDIUM", "student")
    assert created.json()["description"] == ""
    assert summary.status_code == 200
    assert set(summary.json()) == SUMMARY_KEYS
    assert uploaded.status_code == 201
    assert set(uploaded.json()) == UPLOAD_KEYS
    assert uploaded.json()["size"] == len(b"contenido")
    assert health.status_code == 200
    assert set(health.json()) == HEALTH_KEYS
    assert health.json() == {"requestedBy": "student", "status": 200, "body": '{"status":"UP"}'}


def test_h_api_05_seed_runs_once(make_app) -> None:
    with TestClient(make_app()) as client:
        first = client.get("/api/tasks", headers=auth_headers("trainer", "TRAINER")).json()
    with TestClient(make_app()) as client:
        second = client.get("/api/tasks", headers=auth_headers("trainer", "TRAINER")).json()
    assert [task["title"] for task in first] == ["Trainer notes"]
    assert second == first


def test_h_api_05_requires_token_on_every_route(make_app) -> None:
    with TestClient(make_app()) as client:
        statuses = [
            client.get("/api/tasks").status_code,
            client.post("/api/tasks", json={}).status_code,
            client.get("/api/summary").status_code,
            client.post("/api/requirements", files={"file": ("a.txt", b"x")}).status_code,
            client.get("/api/backend-health").status_code,
        ]
    assert statuses == [401] * 5


# H-API-06: contrato multipart y salud con urllib3 simulado
def test_h_api_06_upload_multipart_contract(make_app, tmp_path) -> None:
    with TestClient(make_app()) as client:
        response = client.post(
            "/api/requirements",
            headers=auth_headers(),
            files={"file": ("requisitos.txt", b"Login accesible", "text/plain")},
        )
    assert response.status_code == 201
    assert response.json()["fileName"] == "requisitos.txt"
    assert response.json()["size"] == len(b"Login accesible")
    assert (tmp_path / "uploads" / "requisitos.txt").read_bytes() == b"Login accesible"


def test_h_api_06_backend_health_uses_urllib3_request(make_app, monkeypatch) -> None:
    calls: list[tuple] = []

    def fake_request(self, method, url, **kwargs):
        calls.append((method, url, kwargs.get("timeout")))
        return fake_health_response(503, b"down")

    monkeypatch.setattr(urllib3.PoolManager, "request", fake_request)
    monkeypatch.delenv("AUTH_HEALTH_URL", raising=False)
    with TestClient(make_app()) as client:
        response = client.get("/api/backend-health", headers=auth_headers())
    assert response.json() == {"requestedBy": "student", "status": 503, "body": "down"}
    assert calls == [("GET", "http://localhost:8080/q/health", 3.0)]


# H-API-07: resumen y claves camelCase
def test_h_api_07_summary_counts_and_high_priority_open(make_app) -> None:
    cases = [
        ("HIGH", "TODO"),
        ("HIGH", "IN_PROGRESS"),
        ("HIGH", "DONE"),
        ("HIGH", "ARCHIVED"),
        ("MEDIUM", "TODO"),
    ]
    with TestClient(make_app()) as client:
        for index, (priority, status) in enumerate(cases):
            client.post(
                "/api/tasks",
                headers=auth_headers(),
                json={"title": f"t{index}", "status": status, "priority": priority},
            )
        summary = client.get("/api/summary", headers=auth_headers()).json()
    assert summary["owner"] == "student"
    assert summary["total"] == 2 + len(cases)
    assert summary["byStatus"] == {"TODO": 3, "IN_PROGRESS": 2, "DONE": 1, "ARCHIVED": 1}
    assert summary["highPriorityOpen"] == 3


def test_h_api_07_task_json_uses_camel_case_created_at(make_app) -> None:
    with TestClient(make_app()) as client:
        created = client.post("/api/tasks", headers=auth_headers(), json={"title": "Fecha"}).json()
    assert "createdAt" in created and "created_at" not in created
    assert isinstance(created["id"], int)


# H-API-08: el origen del frontend sigue permitido con credenciales; los demás ya no (ver test_corrections.py)
def test_h_api_08_cors_preflight_for_frontend_origin(make_app) -> None:
    frontend_origin = "http://localhost:4200"
    with TestClient(make_app()) as client:
        response = client.options(
            "/api/tasks",
            headers={"Origin": frontend_origin, "Access-Control-Request-Method": "GET"},
        )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == frontend_origin
    assert response.headers["access-control-allow-credentials"] == "true"


# H-API-09: forma de errores
@pytest.mark.parametrize(
    "raw_token",
    [
        "student|STUDENT|campos-de-menos",
        f"student|STUDENT|{int(time.time()) + ONE_HOUR_SECONDS}|otro-secreto",
        f"student|STUDENT|{int(time.time()) - 1}|{TEST_SECRET}",
        f"student|STUDENT|no-es-numero|{TEST_SECRET}",
    ],
)
def test_h_api_09_rejects_malformed_expired_or_foreign_tokens(make_app, raw_token) -> None:
    token = base64.b64encode(raw_token.encode()).decode()
    with TestClient(make_app()) as client:
        response = client.get("/api/tasks", headers={"Authorization": "Bearer " + token})
    assert response.status_code == 401


def test_h_api_09_invalid_token_response_shape(make_app) -> None:
    with TestClient(make_app()) as client:
        response = client.get("/api/tasks", headers={"Authorization": "Bearer no-es-base64"})
    assert response.status_code == 401
    assert response.json()["detail"].startswith("Invalid token")


def test_h_api_09_backend_health_failure_shape(make_app, monkeypatch) -> None:
    def failing_request(self, method, url, **kwargs):
        raise urllib3.exceptions.HTTPError("fallo-interno-simulado")

    monkeypatch.setattr(urllib3.PoolManager, "request", failing_request)
    with TestClient(make_app()) as client:
        response = client.get("/api/backend-health", headers=auth_headers())
    assert response.status_code == 200
    assert set(response.json()) == HEALTH_KEYS
    assert response.json()["status"] == 0
    assert response.json()["requestedBy"] == "student"


# H-API-10: antes del cambio la API aceptaba cualquier valor; ahora se rechaza con 422
def test_h_api_10_create_task_rejects_values_that_were_accepted_before(make_app) -> None:
    with TestClient(make_app()) as client:
        empty_title = client.post("/api/tasks", headers=auth_headers(), json={"title": "", "status": "LO-QUE-SEA", "priority": "X"})
        numeric_title = client.post("/api/tasks", headers=auth_headers(), json={"title": 123})
        empty_body = client.post("/api/tasks", headers=auth_headers(), json={})
    assert [empty_title.status_code, numeric_title.status_code, empty_body.status_code] == [422, 422, 422]


# H-API-11: ciclo de vida
def test_h_api_11_connection_closed_after_shutdown(make_app) -> None:
    app = make_app()
    with TestClient(app) as client:
        assert client.get("/api/tasks", headers=auth_headers()).status_code == 200
    with pytest.raises(sqlite3.ProgrammingError):
        app.state.connection.execute("SELECT 1")


def test_h_api_11_concurrent_requests_succeed(make_app) -> None:
    requests_count = 16
    with TestClient(make_app()) as client:
        with ThreadPoolExecutor(max_workers=4) as pool:
            statuses = list(
                pool.map(lambda _: client.get("/api/tasks", headers=auth_headers()).status_code, range(requests_count))
            )
    assert statuses == [200] * requests_count
