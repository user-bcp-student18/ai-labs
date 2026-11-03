"""Pruebas por endpoint según docs/ENDPOINTS.md (sección api).

Las pruebas marcadas xfail(strict=True) describen el comportamiento correcto de un hallazgo
que sigue "Pendiente" en HALLAZGOS.md. Hoy fallan por el bug real; no se adaptaron para pasar.
Cuando el hallazgo se corrija, strict=True las hará fallar hasta retirar la marca.
"""

import base64
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest
import urllib3
from fastapi.testclient import TestClient

from app.main import create_app
from tests.test_characterization import TASK_KEYS, TEST_SECRET, auth_headers

ONE_HOUR_SECONDS = 3600
TITLE_MAX_LENGTH = 200
DESCRIPTION_MAX_LENGTH = 2000
ONE_MEBIBYTE = 1024 * 1024
INVALID_TOKEN_BODY = {"detail": "Invalid token"}
INTERNAL_ERROR_TEXT = "Internal Server Error"
INTERNAL_DETAIL = "detalle-interno-que-no-debe-salir"

IDOR_BUG = pytest.mark.xfail(strict=True, reason="H-API-02: la autorización no depende de la identidad del token")
SQL_BUG = pytest.mark.xfail(strict=True, reason="H-API-03: SQL concatenado; una comilla simple provoca 500")
FILE_BUG = pytest.mark.xfail(strict=True, reason="H-API-04: el nombre del archivo no se normaliza")


def raw_token(fields: str) -> str:
    return "Bearer " + base64.b64encode(fields.encode()).decode()


def now_plus(seconds: int) -> int:
    return int(time.time()) + seconds


@pytest.fixture
def app(tmp_path: Path):
    return create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))


@pytest.fixture
def client(app):
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(self.server.reply_status)
        self.end_headers()
        self.wfile.write(self.server.reply_body)

    def log_message(self, *_args) -> None:
        return


@pytest.fixture
def health_server(monkeypatch):
    server = HTTPServer(("127.0.0.1", 0), HealthHandler)
    server.reply_status = 200
    server.reply_body = b'{"status":"UP"}'
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("AUTH_HEALTH_URL", f"http://127.0.0.1:{server.server_port}/q/health")
    yield server
    server.shutdown()
    server.server_close()
    thread.join()


def closed_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


# Autenticación común (401) en los 5 endpoints
ALL_ENDPOINTS = [
    ("GET", "/api/tasks", {}),
    ("POST", "/api/tasks", {"json": {"title": "x"}}),
    ("GET", "/api/summary", {}),
    ("POST", "/api/requirements", {"files": {"file": ("a.txt", b"x", "text/plain")}}),
    ("GET", "/api/backend-health", {}),
]
VALID_TOKEN_FIELDS = f"student|STUDENT|{now_plus(ONE_HOUR_SECONDS)}|{TEST_SECRET}"
INVALID_AUTH_HEADERS = {
    "sin_cabecera": {},
    "no_es_base64": {"Authorization": "Bearer no-es-base64"},
    "pocos_campos": {"Authorization": raw_token("student|STUDENT|solo-tres")},
    "secreto_distinto": {"Authorization": raw_token(f"student|STUDENT|{now_plus(ONE_HOUR_SECONDS)}|otro")},
    "expirado": {"Authorization": raw_token(f"student|STUDENT|{now_plus(-5)}|{TEST_SECRET}")},
    "expiracion_no_numerica": {"Authorization": raw_token(f"student|STUDENT|manana|{TEST_SECRET}")},
    "bearer_minuscula": {"Authorization": "bearer " + raw_token(VALID_TOKEN_FIELDS).split(" ", 1)[1]},
    "esquema_token": {"Authorization": "Token " + raw_token(VALID_TOKEN_FIELDS).split(" ", 1)[1]},
}


@pytest.mark.parametrize("auth_case", INVALID_AUTH_HEADERS)
@pytest.mark.parametrize(("method", "path", "kwargs"), ALL_ENDPOINTS)
def test_every_endpoint_returns_401_for_invalid_credentials(client, method, path, kwargs, auth_case) -> None:
    response = client.request(method, path, headers=INVALID_AUTH_HEADERS[auth_case], **kwargs)
    assert response.status_code == 401
    assert response.json() == INVALID_TOKEN_BODY


def test_authentication_is_checked_before_body_validation(client) -> None:
    invalid_task = client.post("/api/tasks", json={})
    missing_file = client.post("/api/requirements")
    assert invalid_task.status_code == 401
    assert missing_file.status_code == 401


def test_unknown_route_returns_404(client) -> None:
    response = client.get("/api/nada", headers=auth_headers())
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_unsupported_method_returns_405(client) -> None:
    response = client.delete("/api/tasks", headers=auth_headers())
    assert response.status_code == 405
    assert response.json() == {"detail": "Method Not Allowed"}


# Error 500 genérico (se provoca con una falla interna simulada, no con un bug conocido)
@pytest.mark.parametrize(
    ("method", "path", "kwargs", "service", "operation"),
    [
        ("GET", "/api/tasks", {}, "task_service", "list_tasks"),
        ("POST", "/api/tasks", {"json": {"title": "x"}}, "task_service", "create_task"),
        ("GET", "/api/summary", {}, "task_service", "summarize"),
        ("POST", "/api/requirements", {"files": {"file": ("a.txt", b"x", "text/plain")}}, "requirement_service", "store"),
    ],
)
def test_internal_failure_returns_generic_500(app, client, monkeypatch, method, path, kwargs, service, operation) -> None:
    def explode(*_args, **_kwargs):
        raise RuntimeError(INTERNAL_DETAIL)

    monkeypatch.setattr(getattr(app.state, service), operation, explode)
    response = client.request(method, path, headers=auth_headers(), **kwargs)
    assert response.status_code == 500
    assert response.text == INTERNAL_ERROR_TEXT
    assert response.headers["content-type"].startswith("text/plain")
    assert INTERNAL_DETAIL not in response.text


# GET /api/tasks
def test_get_tasks_happy_path_returns_own_seeded_tasks_ordered(client) -> None:
    response = client.get("/api/tasks", headers=auth_headers())
    tasks = response.json()
    assert response.status_code == 200
    assert [task["title"] for task in tasks] == ["Refactor login", "Review API"]
    assert [task["id"] for task in tasks] == sorted(task["id"] for task in tasks)
    assert all(set(task) == TASK_KEYS and task["owner"] == "student" for task in tasks)


def test_get_tasks_includes_a_newly_created_task(client) -> None:
    client.post("/api/tasks", headers=auth_headers(), json={"title": "Nueva tarea"})
    titles = [task["title"] for task in client.get("/api/tasks", headers=auth_headers()).json()]
    assert titles[-1] == "Nueva tarea"


@pytest.mark.parametrize("owner", [None, ""])
def test_get_tasks_without_owner_uses_token_user(client, owner) -> None:
    params = {} if owner is None else {"owner": owner}
    response = client.get("/api/tasks", params=params, headers=auth_headers())
    assert response.status_code == 200
    assert {task["owner"] for task in response.json()} == {"student"}


def test_get_tasks_for_user_without_tasks_returns_empty_list(client) -> None:
    response = client.get("/api/tasks", headers=auth_headers("sin-tareas", "STUDENT"))
    assert response.status_code == 200
    assert response.json() == []


@IDOR_BUG
def test_get_tasks_user_cannot_read_tasks_of_another_owner(client) -> None:
    response = client.get("/api/tasks", params={"owner": "trainer"}, headers=auth_headers("student"))
    leaked = response.status_code == 200 and any(task["owner"] == "trainer" for task in response.json())
    assert not leaked


# POST /api/tasks
def test_post_task_happy_path_with_all_fields_and_persists(client) -> None:
    payload = {"title": "Escribir pruebas", "description": "Cubrir login", "status": "IN_PROGRESS", "priority": "HIGH"}
    created = client.post("/api/tasks", headers=auth_headers(), json=payload)
    listed = client.get("/api/tasks", headers=auth_headers()).json()
    body = created.json()
    assert created.status_code == 201
    assert set(body) == TASK_KEYS
    assert {key: body[key] for key in payload} == payload
    assert body["owner"] == "student"
    assert body in listed


def test_post_task_minimal_payload_applies_defaults(client) -> None:
    body = client.post("/api/tasks", headers=auth_headers(), json={"title": "Solo titulo"}).json()
    assert (body["description"], body["status"], body["priority"], body["owner"]) == ("", "TODO", "MEDIUM", "student")


def test_post_task_accepts_title_and_description_at_their_limits(client) -> None:
    payload = {"title": "t" * TITLE_MAX_LENGTH, "description": "d" * DESCRIPTION_MAX_LENGTH}
    response = client.post("/api/tasks", headers=auth_headers(), json=payload)
    assert response.status_code == 201
    assert response.json()["title"] == payload["title"]


def test_post_task_ignores_unknown_fields(client) -> None:
    response = client.post("/api/tasks", headers=auth_headers(), json={"title": "x", "campo_extra": 1})
    assert response.status_code == 201
    assert "campo_extra" not in response.json()


@pytest.mark.parametrize("status", ["TODO", "IN_PROGRESS", "DONE", "ARCHIVED"])
def test_post_task_accepts_every_documented_status(client, status) -> None:
    response = client.post("/api/tasks", headers=auth_headers(), json={"title": "x", "status": status})
    assert (response.status_code, response.json()["status"]) == (201, status)


@pytest.mark.parametrize("priority", ["HIGH", "MEDIUM", "LOW"])
def test_post_task_accepts_every_documented_priority(client, priority) -> None:
    response = client.post("/api/tasks", headers=auth_headers(), json={"title": "x", "priority": priority})
    assert (response.status_code, response.json()["priority"]) == (201, priority)


@pytest.mark.parametrize(
    ("payload", "field", "error_type"),
    [
        ({}, "title", "missing"),
        ({"title": ""}, "title", "string_too_short"),
        ({"title": "t" * (TITLE_MAX_LENGTH + 1)}, "title", "string_too_long"),
        ({"title": 123}, "title", "string_type"),
        ({"title": "x", "description": "d" * (DESCRIPTION_MAX_LENGTH + 1)}, "description", "string_too_long"),
        ({"title": "x", "status": "LO-QUE-SEA"}, "status", "enum"),
        ({"title": "x", "priority": "URGENT"}, "priority", "enum"),
    ],
)
def test_post_task_invalid_payload_returns_422(client, payload, field, error_type) -> None:
    response = client.post("/api/tasks", headers=auth_headers(), json=payload)
    error = response.json()["detail"][0]
    assert response.status_code == 422
    assert (error["loc"], error["type"]) == (["body", field], error_type)


def test_post_task_malformed_json_returns_422(client) -> None:
    response = client.post(
        "/api/tasks",
        headers={**auth_headers(), "Content-Type": "application/json"},
        content="{no es json",
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "json_invalid"


@IDOR_BUG
def test_post_task_user_cannot_create_task_for_another_owner(client) -> None:
    response = client.post("/api/tasks", headers=auth_headers("student"), json={"title": "x", "owner": "trainer"})
    created_for_other = response.status_code == 201 and response.json()["owner"] != "student"
    assert not created_for_other


@SQL_BUG
def test_post_task_accepts_title_with_apostrophe(client) -> None:
    response = client.post("/api/tasks", headers=auth_headers(), json={"title": "O'Brien"})
    assert response.status_code == 201
    assert response.json()["title"] == "O'Brien"


# GET /api/summary
def test_summary_happy_path_for_seeded_user(client) -> None:
    response = client.get("/api/summary", headers=auth_headers())
    assert response.status_code == 200
    assert response.json() == {"owner": "student", "total": 2, "byStatus": {"TODO": 1, "IN_PROGRESS": 1}, "highPriorityOpen": 1}


def test_summary_for_user_without_tasks_is_empty(client) -> None:
    response = client.get("/api/summary", headers=auth_headers("sin-tareas", "STUDENT"))
    assert response.status_code == 200
    assert response.json() == {"owner": "sin-tareas", "total": 0, "byStatus": {}, "highPriorityOpen": 0}


@pytest.mark.parametrize("closed_status", ["DONE", "ARCHIVED"])
def test_summary_does_not_count_closed_high_priority_tasks(client, closed_status) -> None:
    client.post("/api/tasks", headers=auth_headers(), json={"title": "x", "priority": "HIGH", "status": closed_status})
    summary = client.get("/api/summary", headers=auth_headers()).json()
    assert summary["byStatus"][closed_status] == 1
    assert summary["highPriorityOpen"] == 1


def test_summary_counts_open_high_priority_task(client) -> None:
    client.post("/api/tasks", headers=auth_headers(), json={"title": "x", "priority": "HIGH", "status": "IN_PROGRESS"})
    assert client.get("/api/summary", headers=auth_headers()).json()["highPriorityOpen"] == 2


@pytest.mark.parametrize("owner", [None, ""])
def test_summary_without_owner_uses_token_user(client, owner) -> None:
    params = {} if owner is None else {"owner": owner}
    assert client.get("/api/summary", params=params, headers=auth_headers()).json()["owner"] == "student"


@IDOR_BUG
def test_summary_user_cannot_read_summary_of_another_owner(client) -> None:
    response = client.get("/api/summary", params={"owner": "trainer"}, headers=auth_headers("student"))
    leaked = response.status_code == 200 and response.json()["owner"] == "trainer" and response.json()["total"] > 0
    assert not leaked


# POST /api/requirements
def test_upload_happy_path_stores_file_and_reports_metadata(client, tmp_path) -> None:
    content = "El login debe ser accesible".encode()
    response = client.post(
        "/api/requirements", headers=auth_headers(), files={"file": ("requisitos.txt", content, "text/plain")}
    )
    body = response.json()
    stored = tmp_path / "uploads" / "requisitos.txt"
    assert response.status_code == 201
    assert set(body) == {"owner", "fileName", "storedAt", "size"}
    assert (body["owner"], body["fileName"], body["size"]) == ("student", "requisitos.txt", len(content))
    assert Path(body["storedAt"]) == stored
    assert stored.read_bytes() == content


def test_upload_empty_file_is_stored_with_size_zero(client, tmp_path) -> None:
    response = client.post("/api/requirements", headers=auth_headers(), files={"file": ("vacio.txt", b"", "text/plain")})
    assert response.status_code == 201
    assert response.json()["size"] == 0
    assert (tmp_path / "uploads" / "vacio.txt").read_bytes() == b""


def test_upload_file_without_extension_keeps_its_name(client, tmp_path) -> None:
    response = client.post("/api/requirements", headers=auth_headers(), files={"file": ("LEEME", b"abc", "text/plain")})
    assert response.status_code == 201
    assert response.json()["fileName"] == "LEEME"
    assert (tmp_path / "uploads" / "LEEME").read_bytes() == b"abc"


def test_upload_one_mebibyte_file_reports_exact_size(client) -> None:
    response = client.post(
        "/api/requirements",
        headers=auth_headers(),
        files={"file": ("grande.bin", b"x" * ONE_MEBIBYTE, "application/octet-stream")},
    )
    assert response.status_code == 201
    assert response.json()["size"] == ONE_MEBIBYTE


def test_upload_same_name_overwrites_previous_file(client, tmp_path) -> None:
    client.post("/api/requirements", headers=auth_headers(), files={"file": ("a.txt", b"primero", "text/plain")})
    client.post("/api/requirements", headers=auth_headers(), files={"file": ("a.txt", b"segundo!", "text/plain")})
    assert (tmp_path / "uploads" / "a.txt").read_bytes() == b"segundo!"


def test_upload_without_file_field_returns_422(client) -> None:
    response = client.post("/api/requirements", headers=auth_headers())
    error = response.json()["detail"][0]
    assert response.status_code == 422
    assert (error["loc"], error["type"]) == (["body", "file"], "missing")


@FILE_BUG
def test_upload_filename_cannot_escape_upload_directory(client, tmp_path) -> None:
    client.post("/api/requirements", headers=auth_headers(), files={"file": ("../escape.txt", b"x", "text/plain")})
    assert not (tmp_path / "escape.txt").exists()


@FILE_BUG
def test_upload_filename_with_missing_subdirectory_does_not_return_500(client) -> None:
    response = client.post(
        "/api/requirements", headers=auth_headers(), files={"file": ("subcarpeta/x.txt", b"x", "text/plain")}
    )
    assert response.status_code != 500


# GET /api/backend-health
def test_health_happy_path_reports_auth_service_response(client, health_server) -> None:
    response = client.get("/api/backend-health", headers=auth_headers())
    assert response.status_code == 200
    assert response.json() == {"requestedBy": "student", "status": 200, "body": '{"status":"UP"}'}


def test_health_reports_error_status_of_auth_service_with_200(client, health_server) -> None:
    health_server.reply_status = 503
    health_server.reply_body = b"mantenimiento"
    response = client.get("/api/backend-health", headers=auth_headers())
    assert response.status_code == 200
    assert response.json() == {"requestedBy": "student", "status": 503, "body": "mantenimiento"}


def test_health_with_empty_body_returns_empty_text(client, health_server) -> None:
    health_server.reply_body = b""
    assert client.get("/api/backend-health", headers=auth_headers()).json()["body"] == ""


def test_health_reports_status_zero_when_auth_service_is_unreachable(client, monkeypatch) -> None:
    monkeypatch.setenv("AUTH_HEALTH_URL", f"http://127.0.0.1:{closed_port()}/q/health")
    response = client.get("/api/backend-health", headers=auth_headers())
    assert response.status_code == 200
    assert response.json() == {"requestedBy": "student", "status": 0, "body": "Auth service unavailable"}


def test_health_reports_status_zero_when_body_is_not_utf8(client, health_server) -> None:
    health_server.reply_body = b"\xff\xfe\xfd"
    response = client.get("/api/backend-health", headers=auth_headers())
    assert response.status_code == 200
    assert response.json() == {"requestedBy": "student", "status": 0, "body": "Auth service unavailable"}


def test_health_reports_status_zero_on_timeout(client, monkeypatch) -> None:
    def timing_out(*_args, **_kwargs):
        raise urllib3.exceptions.TimeoutError(INTERNAL_DETAIL)

    monkeypatch.setattr(urllib3.PoolManager, "request", timing_out)
    response = client.get("/api/backend-health", headers=auth_headers())
    assert response.json() == {"requestedBy": "student", "status": 0, "body": "Auth service unavailable"}
    assert INTERNAL_DETAIL not in response.text


def test_health_uses_the_user_of_the_token(client, health_server) -> None:
    assert client.get("/api/backend-health", headers=auth_headers("trainer", "TRAINER")).json()["requestedBy"] == "trainer"
