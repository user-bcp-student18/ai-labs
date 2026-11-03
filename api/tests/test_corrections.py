import logging
import sqlite3
from importlib.metadata import version
from pathlib import Path

import pytest
import urllib3
from fastapi.testclient import TestClient
from packaging.version import Version

from app.main import create_app
from tests.test_characterization import auth_headers

MIN_URLLIB3 = Version("2.8.0")
MIN_PYTHON_MULTIPART = Version("0.0.31")
ALLOWED_ORIGIN = "http://localhost:4200"
FOREIGN_ORIGIN = "http://otro-origen.example"
INTERNAL_FAILURE_TEXT = "fallo-interno-simulado"


@pytest.fixture
def make_app(tmp_path: Path):
    def factory():
        return create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))

    return factory


def preflight(client: TestClient, origin: str):
    return client.options(
        "/api/tasks",
        headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
    )


# H-API-05: capas separadas
def test_h_api_05_repository_owns_persistence(tmp_path: Path) -> None:
    from app.repository import TaskRepository

    repository = TaskRepository(str(tmp_path / "repo.db"))
    repository.init_schema()
    repository.seed_if_empty()
    repository.seed_if_empty()
    seeded = repository.list_by_owner("student")
    created = repository.insert("T", "D", "TODO", "student", "LOW")
    repository.close()
    assert [task.title for task in seeded] == ["Refactor login", "Review API"]
    assert created.id > seeded[-1].id
    assert created.owner == "student"


def test_h_api_05_service_builds_summary_without_http(tmp_path: Path) -> None:
    from app.repository import TaskRepository
    from app.services import TaskService

    repository = TaskRepository(str(tmp_path / "svc.db"))
    repository.init_schema()
    repository.seed_if_empty()
    summary = TaskService(repository).summarize("student")
    repository.close()
    assert summary.owner == "student"
    assert summary.total == 2
    assert summary.high_priority_open == 1


def test_h_api_05_routes_do_not_contain_sql() -> None:
    routes_dir = Path(__file__).resolve().parents[1] / "app" / "routes"
    sources = [path.read_text(encoding="utf-8") for path in routes_dir.glob("*.py")]
    assert sources
    assert not any("execute(" in source or "SELECT" in source for source in sources)


# H-API-06: versiones sin CVEs conocidos
def test_h_api_06_dependencies_meet_fixed_versions() -> None:
    assert Version(version("urllib3")) >= MIN_URLLIB3
    assert Version(version("python-multipart")) >= MIN_PYTHON_MULTIPART


def test_h_api_06_requirements_pin_fixed_versions() -> None:
    requirements = (Path(__file__).resolve().parents[1] / "requirements.txt").read_text(encoding="utf-8")
    pins = dict(line.split("==") for line in requirements.splitlines() if "==" in line)
    assert Version(pins["urllib3"]) >= MIN_URLLIB3
    assert Version(pins["python-multipart"]) >= MIN_PYTHON_MULTIPART


# H-API-07: modelos tipados y reglas sin literales sueltos
def test_h_api_07_openapi_declares_typed_models(make_app) -> None:
    schemas = make_app().openapi()["components"]["schemas"]
    assert {"TaskCreate", "TaskResponse", "SummaryResponse", "UploadResponse", "BackendHealthResponse"} <= set(schemas)


def test_h_api_07_response_models_use_camel_case_aliases(make_app) -> None:
    schemas = make_app().openapi()["components"]["schemas"]
    assert "createdAt" in schemas["TaskResponse"]["properties"]
    assert {"byStatus", "highPriorityOpen"} <= set(schemas["SummaryResponse"]["properties"])
    assert {"fileName", "storedAt"} <= set(schemas["UploadResponse"]["properties"])
    assert "requestedBy" in schemas["BackendHealthResponse"]["properties"]


def test_h_api_07_domain_constants_are_named() -> None:
    from app import config

    assert config.HIGH_PRIORITY == "HIGH"
    assert config.CLOSED_STATUSES == frozenset({"DONE", "ARCHIVED"})


# H-API-08: CORS restringido
def test_h_api_08_listed_origin_is_allowed(make_app) -> None:
    with TestClient(make_app()) as client:
        response = preflight(client, ALLOWED_ORIGIN)
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN


def test_h_api_08_unlisted_origin_is_rejected(make_app) -> None:
    with TestClient(make_app()) as client:
        response = preflight(client, FOREIGN_ORIGIN)
    assert "access-control-allow-origin" not in response.headers


def test_h_api_08_origins_come_from_environment(make_app, monkeypatch) -> None:
    monkeypatch.setenv("WORKSHOP_CORS_ORIGINS", FOREIGN_ORIGIN)
    with TestClient(make_app()) as client:
        allowed = preflight(client, FOREIGN_ORIGIN)
        rejected = preflight(client, ALLOWED_ORIGIN)
    assert allowed.headers["access-control-allow-origin"] == FOREIGN_ORIGIN
    assert "access-control-allow-origin" not in rejected.headers


# H-API-09: errores genéricos, detalle solo en log
def test_h_api_09_invalid_token_detail_is_generic(make_app, caplog) -> None:
    with caplog.at_level(logging.WARNING):
        with TestClient(make_app()) as client:
            response = client.get("/api/tasks", headers={"Authorization": "Bearer no-es-base64"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}
    assert any("token" in record.getMessage().lower() for record in caplog.records)


def test_h_api_09_backend_health_failure_hides_exception(make_app, monkeypatch, caplog) -> None:
    def failing_request(self, method, url, **kwargs):
        raise urllib3.exceptions.HTTPError(INTERNAL_FAILURE_TEXT)

    monkeypatch.setattr(urllib3.PoolManager, "request", failing_request)
    with caplog.at_level(logging.WARNING):
        with TestClient(make_app()) as client:
            response = client.get("/api/backend-health", headers=auth_headers())
    body = response.json()
    assert response.status_code == 200
    assert (body["requestedBy"], body["status"]) == ("student", 0)
    assert INTERNAL_FAILURE_TEXT not in body["body"]
    assert INTERNAL_FAILURE_TEXT in caplog.text


# H-API-10: validación de tareas
@pytest.mark.parametrize(
    "payload",
    [
        {"title": ""},
        {},
        {"title": "T", "status": "LO-QUE-SEA"},
        {"title": "T", "priority": "X"},
        {"title": 123},
    ],
)
def test_h_api_10_rejects_invalid_task_payloads(make_app, payload) -> None:
    with TestClient(make_app()) as client:
        response = client.post("/api/tasks", headers=auth_headers(), json=payload)
    assert response.status_code == 422


def test_h_api_10_valid_payload_keeps_defaults(make_app) -> None:
    with TestClient(make_app()) as client:
        response = client.post("/api/tasks", headers=auth_headers(), json={"title": "Valida"})
    assert response.status_code == 201
    assert response.json()["status"] == "TODO"
    assert response.json()["priority"] == "MEDIUM"
    assert response.json()["owner"] == "student"


# H-API-11: ciclo de vida y recursos
def test_h_api_11_uses_lifespan_instead_of_on_event(make_app) -> None:
    assert make_app().router.on_shutdown == []


def test_h_api_11_pool_manager_is_reused(make_app, monkeypatch) -> None:
    created: list[object] = []

    class CountingPool(urllib3.PoolManager):
        def __init__(self, *args, **kwargs):
            created.append(self)
            super().__init__(*args, **kwargs)

        def request(self, method, url, **kwargs):
            raise urllib3.exceptions.HTTPError(INTERNAL_FAILURE_TEXT)

    monkeypatch.setattr(urllib3, "PoolManager", CountingPool)
    with TestClient(make_app()) as client:
        for _ in range(3):
            client.get("/api/backend-health", headers=auth_headers())
    assert len(created) == 1


def test_h_api_11_connection_closed_after_shutdown(make_app) -> None:
    app = make_app()
    with TestClient(app) as client:
        client.get("/api/tasks", headers=auth_headers())
    with pytest.raises(sqlite3.ProgrammingError):
        app.state.connection.execute("SELECT 1")
