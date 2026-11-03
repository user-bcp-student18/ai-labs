# Pruebas de ReqFlow

Este archivo registra las pruebas por componente. Cada componente mantiene solo su sección.

## api

Pruebas de la API FastAPI (`api/tests/`). Se ejecutan con cwd `api/` (o, desde la raíz, con `python tools/lab.py test api`, que usa el mismo `python -m pytest` del entorno `api/.venv`). Fecha de las ejecuciones: 2026-11-02, Python 3.13.15, Windows.

Fuente de las expectativas: la sección api de [docs/ENDPOINTS.md](./ENDPOINTS.md). No se probó ningún endpoint ni comportamiento que ese documento no describa.

### Archivos de pruebas

| Archivo | Contenido | Pruebas |
|---|---|---|
| [api/tests/test_endpoints.py](../api/tests/test_endpoints.py) | Camino feliz, casos borde y errores por endpoint según `docs/ENDPOINTS.md` (este paso). | 101 (95 pasan, 6 `xfail`) |
| `api/tests/test_api.py`, `test_characterization.py`, `test_corrections.py` | Pruebas originales, de caracterización (antes del refactor) y de corrección de H-API-05 a H-API-11. | 43 (todas pasan) |

### Tabla de pruebas por endpoint

Todas son de `api/tests/test_endpoints.py`. "Resultado" indica lo ejecutado: **pasa** o **xfail** (falla hoy por un bug conocido; ver "Fallos conocidos").

#### Comunes a los 5 endpoints

| Endpoint | Caso | Tipo | Resultado esperado | Resultado |
|---|---|---|---|---|
| todos | Sin cabecera, token no Base64, pocos campos, secreto distinto, expirado, expiración no numérica, `bearer` en minúscula, esquema `Token` (8 casos × 5 endpoints = 40) | Error | 401 y cuerpo `{"detail": "Invalid token"}` | pasa |
| `POST /api/tasks`, `POST /api/requirements` | Cuerpo inválido sin token (`{}`; sin archivo) | Borde | 401 (la autenticación se evalúa antes que la validación) | pasa |
| ruta inexistente | `GET /api/nada` | Error | 404 `{"detail": "Not Found"}` | pasa |
| `/api/tasks` | `DELETE` | Error | 405 `{"detail": "Method Not Allowed"}` | pasa |
| tareas, resumen, subida (4 casos) | Falla interna simulada en el servicio | Error | 500, cuerpo de texto `Internal Server Error` (`text/plain`) sin el detalle de la excepción | pasa |

#### GET /api/tasks

| Caso | Tipo | Resultado esperado | Resultado |
|---|---|---|---|
| Usuario con datos semilla | Feliz | 200; 2 tareas propias ordenadas por `id`, con las 7 claves documentadas | pasa |
| Tarea recién creada | Feliz | Aparece al final de la lista | pasa |
| `owner` omitido o `""` | Borde | Devuelve las tareas del usuario del token | pasa |
| Usuario sin tareas | Borde | 200 y `[]` | pasa |
| Token inválido | Error | 401 (ver tabla común) | pasa |
| Falla interna | Error | 500 genérico (ver tabla común) | pasa |
| Un usuario pide `owner=trainer` | Seguridad | No debe recibir las tareas de `trainer` | **xfail** (H-API-02) |

#### POST /api/tasks

| Caso | Tipo | Resultado esperado | Resultado |
|---|---|---|---|
| Todos los campos | Feliz | 201, mismos valores, `owner` = usuario del token y la tarea aparece en `GET /api/tasks` | pasa |
| Solo `title` | Feliz | 201 con defaults `description=""`, `status=TODO`, `priority=MEDIUM` | pasa |
| `title` de 200 y `description` de 2000 caracteres | Borde | 201 | pasa |
| Campo desconocido | Borde | 201 y el campo se ignora | pasa |
| Cada `status` (4) y cada `priority` (3) documentados | Borde | 201 con el valor enviado | pasa |
| Payload vacío `{}`, `title` vacío, `title` de 201, `title` numérico, `description` de 2001, `status` inválido, `priority` inválida (7 casos) | Error | 422 con `loc` y `type` del campo (`missing`, `string_too_short`, `string_too_long`, `string_type`, `enum`) | pasa |
| JSON mal formado | Error | 422 con `type: json_invalid` | pasa |
| Token inválido / falla interna | Error | 401 / 500 genérico | pasa |
| Un usuario crea una tarea con `owner` de otro | Seguridad | No debe crearse a nombre de otro usuario | **xfail** (H-API-02) |
| `title` con apóstrofe (`O'Brien`) | Borde | 201 y el título se conserva | **xfail** (H-API-03) |

#### GET /api/summary

| Caso | Tipo | Resultado esperado | Resultado |
|---|---|---|---|
| Usuario semilla | Feliz | 200 `{"owner": "student", "total": 2, "byStatus": {"TODO": 1, "IN_PROGRESS": 1}, "highPriorityOpen": 1}` | pasa |
| Usuario sin tareas | Borde | `total 0`, `byStatus {}`, `highPriorityOpen 0` | pasa |
| Tarea `HIGH` en `DONE` o `ARCHIVED` (2 casos) | Borde | Cuenta en `byStatus`, no en `highPriorityOpen` | pasa |
| Tarea `HIGH` en `IN_PROGRESS` | Borde | `highPriorityOpen` pasa de 1 a 2 | pasa |
| `owner` omitido o `""` | Borde | `owner` del resultado = usuario del token | pasa |
| Token inválido / falla interna | Error | 401 / 500 genérico | pasa |
| Un usuario pide `owner=trainer` | Seguridad | No debe recibir el resumen de `trainer` | **xfail** (H-API-02) |

#### POST /api/requirements

| Caso | Tipo | Resultado esperado | Resultado |
|---|---|---|---|
| Archivo `.txt` válido | Feliz | 201 con `owner`, `fileName`, `storedAt` (ruta dentro de `uploads/`) y `size`; contenido guardado idéntico | pasa |
| Archivo vacío | Borde | 201 con `size` 0 y archivo vacío | pasa |
| Archivo sin extensión (`LEEME`) | Borde | 201 y se conserva el nombre | pasa |
| Archivo de 1 MiB | Borde | 201 con `size` 1 048 576 | pasa |
| Mismo nombre dos veces (mismo usuario) | Borde | 409 `{"detail": "File already exists"}` sin filtrar la ruta; el primer archivo queda intacto | pasa |
| Mismo nombre de otro usuario (H-API-15) | Seguridad | 409; el archivo del primer usuario queda intacto | pasa |
| Token inválido sin archivo escrito | Error | 401 y el directorio de cargas queda vacío | pasa |
| Subidas concurrentes del mismo nombre (servicio, 8 hilos) | Borde | Exactamente una tiene éxito y 7 se rechazan | pasa |
| Fallo de escritura simulado (servicio) | Error | No queda archivo parcial y un reintento posterior funciona | pasa |
| Sin campo `file` | Error | 422 con `loc: ["body", "file"]`, `type: missing` | pasa |
| Token inválido / falla interna | Error | 401 / 500 genérico | pasa |
| Nombre con `../` | Seguridad | No debe escribirse fuera de `uploads/` | **xfail** (H-API-04) |
| Nombre con subdirectorio inexistente (`subcarpeta/x.txt`) | Error | No debe devolver 500 | **xfail** (H-API-04) |

#### GET /api/backend-health

Las pruebas usan un servidor HTTP local efímero (`127.0.0.1`, puerto libre) como servicio de autenticación; ninguna llama a la red externa.

| Caso | Tipo | Resultado esperado | Resultado |
|---|---|---|---|
| Auth responde 200 `{"status":"UP"}` | Feliz | 200 `{"requestedBy": "student", "status": 200, "body": "{\"status\":\"UP\"}"}` | pasa |
| Auth responde 503 | Borde | 200 con `status` 503 y el cuerpo recibido | pasa |
| Auth responde cuerpo vacío | Borde | `body: ""` | pasa |
| Auth inalcanzable (puerto cerrado) | Error | 200 con `status 0` y `body: "Auth service unavailable"` | pasa |
| Cuerpo que no es UTF-8 | Error | 200 con `status 0` y el texto fijo | pasa |
| Tiempo agotado simulado | Error | 200 con `status 0`, sin el detalle de la excepción | pasa |
| `requestedBy` con otro usuario del token | Borde | Refleja el `usuario` del token | pasa |
| Token inválido | Error | 401 (ver tabla común) | pasa |

`docs/ENDPOINTS.md` no documenta otros errores para este endpoint, por lo que no hay más pruebas de error.

#### Cobertura de las respuestas de error documentadas

| Respuesta documentada | Prueba |
|---|---|
| 401 (los 5 endpoints) | `test_every_endpoint_returns_401_for_invalid_credentials` |
| 404, 405 | `test_unknown_route_returns_404`, `test_unsupported_method_returns_405` |
| 422 de `POST /api/tasks` | `test_post_task_invalid_payload_returns_422`, `test_post_task_malformed_json_returns_422` |
| 422 de `POST /api/requirements` | `test_upload_without_file_field_returns_422` |
| 500 genérico (texto, sin detalle) | `test_internal_failure_returns_generic_500` |
| 500 por comilla en `owner`, `title` o `description` (documentado como riesgo) | `test_post_task_accepts_title_with_apostrophe` (**xfail**, H-API-03). No se escribió una prueba que exija el 500: eso daría por buena la falla. |
| 500 por subdirectorio en el nombre del archivo (documentado como riesgo) | `test_upload_filename_with_missing_subdirectory_does_not_return_500` (**xfail**, H-API-04) |
| Un usuario no puede leer tareas de otro `owner` | `test_get_tasks_user_cannot_read_tasks_of_another_owner` y `test_summary_user_cannot_read_summary_of_another_owner` (**xfail**, H-API-02) |

CORS (origen permitido, rechazado y por variable de entorno) y los demás casos de H-API-05 a H-API-11 los cubren las pruebas de `test_corrections.py` y `test_characterization.py`; no se duplican aquí.

### Código de las pruebas

Código completo: [api/tests/test_endpoints.py](../api/tests/test_endpoints.py). Se incluyen aquí las partes que definen el criterio (marcas de fallos conocidos y las pruebas de seguridad). El resto sigue el mismo patrón `cliente → petición → afirmaciones`.

```python
IDOR_BUG = pytest.mark.xfail(strict=True, reason="H-API-02: la autorización no depende de la identidad del token")
SQL_BUG = pytest.mark.xfail(strict=True, reason="H-API-03: SQL concatenado; una comilla simple provoca 500")
FILE_BUG = pytest.mark.xfail(strict=True, reason="H-API-04: el nombre del archivo no se normaliza")


@pytest.fixture
def client(app):
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.mark.parametrize("auth_case", INVALID_AUTH_HEADERS)
@pytest.mark.parametrize(("method", "path", "kwargs"), ALL_ENDPOINTS)
def test_every_endpoint_returns_401_for_invalid_credentials(client, method, path, kwargs, auth_case) -> None:
    response = client.request(method, path, headers=INVALID_AUTH_HEADERS[auth_case], **kwargs)
    assert response.status_code == 401
    assert response.json() == INVALID_TOKEN_BODY


@IDOR_BUG
def test_get_tasks_user_cannot_read_tasks_of_another_owner(client) -> None:
    response = client.get("/api/tasks", params={"owner": "trainer"}, headers=auth_headers("student"))
    leaked = response.status_code == 200 and any(task["owner"] == "trainer" for task in response.json())
    assert not leaked


@IDOR_BUG
def test_summary_user_cannot_read_summary_of_another_owner(client) -> None:
    response = client.get("/api/summary", params={"owner": "trainer"}, headers=auth_headers("student"))
    leaked = response.status_code == 200 and response.json()["owner"] == "trainer" and response.json()["total"] > 0
    assert not leaked


@FILE_BUG
def test_upload_filename_cannot_escape_upload_directory(client, tmp_path) -> None:
    client.post("/api/requirements", headers=auth_headers(), files={"file": ("../escape.txt", b"x", "text/plain")})
    assert not (tmp_path / "escape.txt").exists()


def test_health_reports_status_zero_when_body_is_not_utf8(client, health_server) -> None:
    health_server.reply_body = b"\xff\xfe\xfd"
    response = client.get("/api/backend-health", headers=auth_headers())
    assert response.status_code == 200
    assert response.json() == {"requestedBy": "student", "status": 0, "body": "Auth service unavailable"}
```

Las pruebas de seguridad aceptan cualquier corrección válida (rechazo con 4xx o filtrado a las tareas propias): solo exigen que no se filtre la información de otro usuario. Con `strict=True`, cuando se corrija el hallazgo la prueba pasará "inesperadamente", `pytest` fallará y habrá que retirar la marca `xfail`.

### Ejecuciones (componente api)

Todas con Python 3.13.15 y `api/.venv`. Las ejecuciones de este paso:

| # | IDs | Comando | Directorio | Salida | Resultado |
|---|---|---|---|---|---|
| 1 | H-API-02, 03, 04 y endpoints | `python -m pytest tests/test_endpoints.py -p no:cacheprovider -W ignore -q -rxXfE` | `api/` | 0 | 91 passed, 6 xfailed |
| 2 | H-API-02, 03, 04 | `python -m pytest tests/test_endpoints.py --runxfail -p no:cacheprovider -W ignore -q` | `api/` | 1 (esperado) | Los 6 tests `xfail` fallan con el bug: `assert not True` (3 de `owner`), `500 == 201` (apóstrofe), `escape.txt` existe fuera de `uploads/` y `500 != 500` (subdirectorio) |
| 3 | todos los endpoints, H-API-05 a H-API-11 | `python tools/lab.py test api` (ejecuta `python -m pytest --cov=app --cov-report=term-missing --cov-report=html --cov-fail-under=85`) | raíz | 0 | 134 passed, 6 xfailed; umbral 85% alcanzado; informe HTML en `api/htmlcov/index.html` |
| 4 | todos | `python -m pytest tests/test_endpoints.py --cov=app --cov-branch -p no:cacheprovider -W ignore -q --cov-report=term-missing` | `api/` | 0 | cobertura 100% (269/269 sentencias, 10/10 ramas) usando solo el archivo nuevo |
| 5 | todos | `python -m pytest tests -p no:cacheprovider -W ignore` | `api/` | 0 | 134 passed, 6 xfailed |
| 6 | H-API-15 (línea base, antes del cambio) | `python tools/lab.py test api` | raíz | 0 | 134 passed, 6 xfailed; cobertura 100% (269 sentencias) |
| 7 | H-API-15 (prueba de caracterización) | `python -m pytest tests/test_endpoints.py -k upload -p no:cacheprovider --no-cov` | `api/` | 0 | 6 passed, 3 xfailed (los 2 de H-API-04 y el nuevo de H-API-15, que describe el defecto contra el código antiguo) |
| 8 | H-API-15 (tras el cambio) | `python tools/lab.py test api` | raíz | 0 | 138 passed, 6 xfailed; cobertura 100% (284 sentencias, 0 sin cubrir); umbral 85% alcanzado |

El resumen detallado de las ejecuciones anteriores (línea base, caracterización, corrección) está en `PLAN.md`, sección "Registro de ejecuciones".

### Cobertura

| Métrica | Numerador | Denominador | Porcentaje | Método |
|---|---|---|---|---|
| **Código modificado** (los 11 módulos de `api/app/` modificados o nuevos respecto a `main`: `main.py` modificado; `config.py`, `dependencies.py`, `repository.py`, `routes/{health,requirements,tasks}.py`, `schemas.py`, `security.py`, `services.py` nuevos) — sentencias | 269 | 269 | 100% | `pytest-cov` con `--cov=app`, medición de ramas activada en `api/pyproject.toml` (`branch = true`); cifras por archivo con `python -m coverage json` tras la ejecución n.º 3 |
| Código modificado — ramas | 10 | 10 | 100% | Igual |
| **Global** (todo `api/app/`, la métrica del gate de `tools/lab.py`, umbral 85%) | 269 | 269 | 100% | Salida de la ejecución n.º 3: "Total coverage: 100.00%" |
| Solo `test_endpoints.py` (informativo) | 269 | 269 | 100% | Ejecución n.º 4 |

Aclaraciones:

- Las dos primeras métricas coinciden porque en el refactor se modificó o creó todo el paquete `app/`; este paso solo añadió pruebas y no modificó código de `app/`.
- La cobertura del código modificado se midió por archivo completo, no línea a línea del diff. Con `main.py` reescrito casi por completo y el resto nuevo, la diferencia sería nula, pero no se calculó por líneas del diff.
- El 100% es de cobertura de líneas y ramas; no demuestra que las pruebas cubran los riesgos pendientes (H-API-01 a H-API-04), que hoy se registran como `xfail`.

### Fallos conocidos (bugs reportados aparte)

Seis pruebas describen el comportamiento correcto y fallan hoy por bugs reales. Se marcan `xfail(strict=True)` y no se adaptaron para pasar. En `HALLAZGOS.md` los hallazgos siguen "Pendiente".

| Prueba | Hallazgo | Comportamiento actual comprobado | Comportamiento correcto que exige la prueba |
|---|---|---|---|
| `test_get_tasks_user_cannot_read_tasks_of_another_owner` | H-API-02 | `GET /api/tasks?owner=trainer` con token de `student` devuelve las tareas de `trainer` | No filtrar tareas de otro usuario |
| `test_summary_user_cannot_read_summary_of_another_owner` | H-API-02 | `GET /api/summary?owner=trainer` devuelve el resumen de `trainer` (`total` 1) | No filtrar el resumen de otro usuario |
| `test_post_task_user_cannot_create_task_for_another_owner` | H-API-02 | `POST /api/tasks` con `owner: "trainer"` crea la tarea a nombre de `trainer` | No crear tareas a nombre de otro usuario |
| `test_post_task_accepts_title_with_apostrophe` | H-API-03 | Un título legítimo con apóstrofe devuelve 500 | 201 y el título se conserva |
| `test_upload_filename_cannot_escape_upload_directory` | H-API-04 | `../escape.txt` escribe un archivo fuera de `uploads/` | No escribir fuera de `uploads/` |
| `test_upload_filename_with_missing_subdirectory_does_not_return_500` | H-API-04 | `subcarpeta/x.txt` devuelve 500 | No devolver 500 |

### Pendientes

- No hay límite de tamaño ni de extensión en `POST /api/requirements` (`docs/ENDPOINTS.md`, pregunta abierta 5); por eso no existe una prueba de "archivo que supera el límite". Solo se probó un archivo de 1 MiB.
- Falta una prueba de que un token con firma inválida se rechaza: depende de la solución de H-API-01 (formato final del token).
- Los casos documentados como observados pero discutibles no se convirtieron en pruebas para no dar por buenos comportamientos dudosos: `owner: ""` crea una tarea con propietario vacío, y un token enviado sin el prefijo `Bearer ` se acepta.
- Las pruebas no se han verificado contra `web` ni `auth` (fuera del alcance); la revisión humana de las pruebas está pendiente.
- `pytest` invocado sin `python -m` falla en la recolección porque `tests/` importa `app` desde el directorio actual; con `python -m pytest` (que usa `tools/lab.py`) funciona. Ya ocurría con los tests originales.

### Pruebas propuestas (no implementadas)

| Endpoint | Prueba | Depende de |
|---|---|---|
| `POST /api/requirements` | Archivo mayor al límite → 413 u otro código acordado | Decisión del límite (H-API-04) |
| `POST /api/requirements` | Extensión no permitida (p. ej. `.exe`) → rechazo | Lista de extensiones (H-API-04) |
| `POST /api/requirements` | El nombre guardado se normaliza y `storedAt` no expone la ruta absoluta | H-API-04 |
| todos | Token con firma inválida, emisor o audiencia incorrectos → 401 | H-API-01 |
| `GET /api/tasks`, `GET /api/summary` | `owner` ajeno → 403 o ignorado, con el código acordado | Decisión de H-API-02 |
| `GET /api/tasks`, `POST /api/tasks`, `GET /api/summary` | Comillas y otros caracteres especiales en `owner` y `description` no producen 500 | H-API-03 |
| `GET /api/backend-health` | `AUTH_HEALTH_URL` inválida (esquema no HTTP) → `status 0` | Confirmar el comportamiento esperado |

### Documentos consultados

`docs/ENDPOINTS.md` (fuente de las expectativas), `AGENTS.md`, `README.md`, `RETO.md`, `docs/GOOD_PRACTICES.md`, `HALLAZGOS.md` y `PLAN.md`. Del código, solo `api/` (`api/app/` para validar nombres y comportamientos, `api/tests/`, `api/pyproject.toml`).
