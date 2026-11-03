# Plan de corrección

Cada componente mantiene su propio apartado. No se renumeran IDs de `HALLAZGOS.md`.

## api

Estado: H-API-05 a H-API-11 implementados (revisión humana del diff pendiente).

**Aprobación humana (2026-11-02 16:46):** respuesta del usuario "aprobar" a la solicitud de aprobación explícita de H-API-05 a H-API-11. Interpretación registrada: se aprueban los 7 IDs con las propuestas tal como están en este plan (incluidos H-API-08 CORS con `http://localhost:4200` por defecto, H-API-09 mensajes genéricos y H-API-10 validación estricta). Las versiones de H-API-06 se confirmarán con la fuente de advisories antes de cambiarlas.

### Alcance de este plan

Hallazgos de `HALLAZGOS.md` en estado "Pendiente": H-API-05 a H-API-11. H-API-01 a H-API-04 (token, `owner`, SQL, archivos) quedan fuera de este plan y se planifican aparte; las dependencias entre ambos grupos se señalan abajo.

### Reglas que aplican a todos los cambios

- **Contrato:** `docs/ENDPOINTS.md` no existe. Se preserva el comportamiento observado: rutas `GET/POST /api/tasks`, `GET /api/summary`, `POST /api/requirements`, `GET /api/backend-health`; códigos 200/201/401; claves JSON `id,title,description,status,owner,priority,createdAt`, `owner,total,byStatus,highPriorityOpen`, `owner,fileName,storedAt,size`, `requestedBy,status,body`. Todo cambio observable se marca "Cambio de contrato" y espera aprobación humana.
- **Convenciones:** solo las de `docs/GOOD_PRACTICES.md` (api) y `AGENTS.md`. Lo que no figura ahí (CORS, `lifespan`) se marca "Requiere decisión".
- **Clean code (AGENTS.md):** una responsabilidad por función, sin duplicación, guard clauses en lugar de anidamiento, constantes con nombre en lugar de literales.
- **Dependencias nuevas:** ninguna. Solo se cambian versiones de `urllib3` y `python-multipart` (H-API-06).
- **Pruebas:** la prueba de caracterización de cada hallazgo se escribe primero y debe pasar contra el código actual. Las pruebas existentes en `api/tests/test_api.py` cubren solo listado, creación y resumen básico, subida simple y 401 con token inválido. Las nuevas van en `api/tests/test_characterization.py` (archivo nuevo, mismo estilo `create_app(tmp_path...)` + `TestClient`). Ejecución: `python tools/lab.py test api` desde la raíz (o `pytest` con cwd `api/`). La meta es 85% del código modificado; el gate de toda la app permanece como está. No se registran resultados hasta ejecutarlos.

### Estructura objetivo (H-API-05, base del resto)

```
api/app/
  main.py          # create_app: solo cableado (CORS, routers, lifespan)
  config.py        # constantes y lectura de variables de entorno
  schemas.py       # modelos Pydantic de request/response
  security.py      # legacy_identity (sin cambiar su lógica aquí; ver H-API-01)
  repository.py    # TaskRepository: único lugar con SQL
  services.py      # TaskService: reglas y cálculo de resumen
  routes/{tasks,requirements,health}.py   # APIRouter, sin SQL ni reglas
```

Orden recomendado: (1) pruebas de caracterización de todos los hallazgos; (2) H-API-06; (3) H-API-07+05 (tipos y capas, mismo movimiento de código); (4) H-API-09; (5) H-API-10; (6) H-API-08; (7) H-API-11. Se recomienda ejecutar antes H-API-01 a H-API-04 para no copiar a `repository.py` el SQL concatenado ni la lógica del token; si no es posible, el movimiento de código no puede cambiar su comportamiento y esas líneas quedan marcadas como pendientes.

---

### H-API-05 — Rutas, SQLite, reglas y serialización en un solo módulo (Refactor, media)

- **Hallazgo:** H-API-05 en `HALLAZGOS.md`. Evidencia: `api/app/main.py:29`, `api/app/main.py:35`, `api/app/main.py:56`, `api/app/main.py:67`, `api/app/main.py:77`, `api/app/main.py:90`, `api/app/main.py:107`.
- **Problema:** `create_app` crea la BD, el esquema y las semillas (`api/app/main.py:35-43`), declara CORS y rutas, ejecuta SQL, aplica reglas (`api/app/main.py:94-104`) y serializa (`api/app/main.py:56-65`) en un cierre de ~100 líneas. No se puede probar ni cambiar una capa sin tocar las demás.
- **Cambio propuesto:** separar en rutas → servicio → repositorio, según `docs/GOOD_PRACTICES.md` ("Nada de SQL directo dentro de la función de la ruta").
  - `TaskRepository(connection)`: `init_schema()`, `seed_if_empty()`, `list_by_owner()`, `insert()`, `get_by_id()`, `statuses_and_priorities_by_owner()`, `close()`. Toda la BD vive aquí.
  - `TaskService(repository)`: `list_tasks`, `create_task`, `summarize`. Sin FastAPI.
  - Routers delgados que reciben/entregan modelos de `schemas.py` y delegan al servicio. Las rutas conservan paths, status codes y nombres de claves.
  - `create_app(db_path, upload_dir)` mantiene su firma y `app.state.connection` / `app.state.upload_dir` (`api/app/main.py:46-47`), porque las pruebas existentes la usan.
  - Una función = una responsabilidad; los literales `"TODO"`, `"HIGH"`, etc. pasan a constantes (ver H-API-07).
- **Archivos a tocar (todos en `api/`):** `app/main.py`; nuevos `app/config.py`, `app/schemas.py`, `app/repository.py`, `app/services.py`, `app/routes/*.py`, `app/routes/__init__.py`; tests.
- **Prueba de caracterización previa:** `test_characterization_routes_and_shapes`: contra el código actual comprueba, para cada ruta, status code y conjunto exacto de claves del JSON (listado con tareas semilla `student` = 2 con orden por `id`; creación 201 con defaults `status=TODO`, `priority=MEDIUM`, `owner=student`; `summary` con `total`, `byStatus`, `highPriorityOpen`; `requirements` 201 con las cuatro claves; `backend-health` 200). También `test_seed_runs_once`: recrear `create_app` sobre la misma BD no duplica semillas (`api/app/main.py:38-39`). Estas pruebas deben seguir en verde sin cambios tras el refactor.
- **Riesgo/Notas:** `app = create_app()` (`api/app/main.py:130`) debe seguir existiendo para el arranque actual (ver H-API-11).

---

### H-API-06 — Dependencias `urllib3 2.5.0` y `python-multipart 0.0.21` (Sugerencia, baja)

- **Hallazgo:** H-API-06. Evidencia: `api/requirements.txt:4`, `api/requirements.txt:5`; uso en `api/app/main.py:10`, `api/app/main.py:118` (urllib3) y `api/app/main.py:108` (carga multipart vía FastAPI).
- **Problema:** `RETO.md` señala ambas versiones, pero aún no hay advisories confirmados ni versión corregida. Estimar CVEs sin consultar la fuente sería inventar evidencia.
- **Cambio propuesto:**
  1. Consultar advisories (GitHub Advisory Database/OSV, o `pip-audit` si se justifica su uso puntual; no se agrega a `requirements-dev.txt` sin justificación) para ambos paquetes y registrar CVE, rango afectado y versión corregida mínima en `HALLAZGOS.md`.
  2. Elegir la versión corregida más baja compatible con `fastapi==0.128.2` y Python 3.13 y actualizar `api/requirements.txt` (y `requirements-dev.txt` solo si los pinea). Sin otras dependencias nuevas.
  3. Si no se confirma ninguna vulnerabilidad, registrar "No aplica" con la fuente consultada; no cambiar versiones.
  4. No silenciar advisories.
- **Archivos a tocar:** `api/requirements.txt` (condicional); `HALLAZGOS.md`; `docs/TESTING.md` si se registra la ejecución.
- **Prueba de caracterización previa:** `test_upload_multipart_contract` (subida multipart devuelve 201 con claves y tamaño correcto, archivo escrito) y `test_backend_health_with_mocked_urllib3` (con `monkeypatch` sobre `urllib3.PoolManager.request`, devuelve `requestedBy/status/body`). Se ejecutan antes y después de subir versiones para detectar regresiones de comportamiento.
- **Pendiente:** versiones objetivo y CVEs, por confirmar con la fuente; la instalación requiere entorno `api/.venv` preparado (`python tools/lab.py setup api`).

---

### H-API-07 — `dict`/`Any`, excepciones amplias, anidamiento y duplicación (Refactor, baja)

- **Hallazgo:** H-API-07. Evidencia: `api/app/main.py:17`, `api/app/main.py:25`, `api/app/main.py:56`, `api/app/main.py:78`, `api/app/main.py:94`, `api/app/main.py:101-103`.
- **Problema:** firmas con `dict[str, Any]`, `except Exception` (`api/app/main.py:25`, `api/app/main.py:120`), tres `if` anidados para `highPriorityOpen`, conteo manual con `if/else`, y literales `"HIGH"`, `"DONE"`, `"ARCHIVED"` repetidos.
- **Cambio propuesto (modelos Pydantic, `docs/GOOD_PRACTICES.md`):**
  - `schemas.py`: `TaskResponse` (campo `created_at` con alias `createdAt`), `TaskCreate`, `SummaryResponse` (`owner`, `total`, `by_status` alias `byStatus`, `high_priority_open` alias `highPriorityOpen`), `UploadResponse` (`fileName`, `storedAt` por alias), `BackendHealthResponse` (`requestedBy`). Rutas con `response_model` y `response_model_by_alias=True` para mantener las claves camelCase.
  - Constantes con nombre: `HIGH_PRIORITY`, `CLOSED_STATUSES = frozenset({"DONE", "ARCHIVED"})`, `DEFAULT_STATUS`, `DEFAULT_PRIORITY`, timeout de salud (`3.0`), URL por defecto de salud.
  - `summarize` en `services.py`: `Counter` para `byStatus` y una condición combinada para `highPriorityOpen`, sin anidamiento; una sola función `as_task` en el repositorio/mapper para evitar duplicar el SELECT de columnas (`api/app/main.py:70`, `api/app/main.py:87`).
  - Excepciones concretas: en el token `ValueError`, `binascii.Error`, `UnicodeDecodeError` (la lógica del token en sí pertenece a H-API-01); en salud, `urllib3.exceptions.HTTPError` y `UnicodeDecodeError`. Cualquier otra excepción propaga y la maneja FastAPI (500 genérico).
  - Identity tipada sin cambiar el acceso `identity["username"]` que exige GOOD_PRACTICES (p. ej. `TypedDict`), sin tocar la lógica del token.
- **Archivos a tocar:** `app/schemas.py`, `app/services.py`, `app/repository.py`, `app/routes/*.py`, `app/config.py`, `app/security.py`; tests.
- **Prueba de caracterización previa:** `test_summary_counts_and_high_priority_open`: crea tareas con combinaciones (`HIGH` con `TODO`, `IN_PROGRESS`, `DONE`, `ARCHIVED`; `MEDIUM`) y verifica `total`, `byStatus` y `highPriorityOpen` exactos; `test_task_json_keys_use_camel_case` (`createdAt`).
- **Riesgo:** orden de claves y tipos en JSON; cubierto con las pruebas anteriores.

---

### H-API-08 — CORS abierto con credenciales (Vulnerabilidad, media) — Requiere decisión

- **Hallazgo:** H-API-08. Evidencia: `api/app/main.py:48`, `api/app/main.py:50`, `api/app/main.py:51`.
- **Problema:** `allow_origins=["*"]` con `allow_credentials=True`, métodos y cabeceras abiertos. `docs/GOOD_PRACTICES.md` no define una regla de CORS, así que lo propuesto es una decisión a aprobar, no una convención existente.
- **Cambio propuesto:** mover CORS a `config.py` leyendo orígenes permitidos de la variable de entorno `WORKSHOP_CORS_ORIGINS` (lista separada por comas); `allow_methods` limitado a `GET, POST, OPTIONS` y `allow_headers` a `Authorization, Content-Type` (los realmente usados por las rutas). Valor por defecto propuesto: `http://localhost:4200` (origen de la web según `README.md`); nunca `*` con credenciales. Sin secretos en el código.
- **Archivos a tocar:** `app/config.py`, `app/main.py`; tests. `compose.yaml`/`web` están fuera del alcance: si el despliegue usa otro origen, se coordina con el responsable de esos componentes y no se modifican aquí.
- **Prueba de caracterización previa:** `test_cors_preflight_current_behavior` (preflight `OPTIONS /api/tasks` con `Origin` y `Access-Control-Request-Method`; registra las cabeceras `access-control-allow-*` actuales). Tras el cambio, cambia deliberadamente: origen permitido responde con su origen; origen no permitido no recibe `access-control-allow-origin`.
- **Cambio de contrato:** sí (cabeceras CORS para orígenes no listados). Requiere aprobación humana y confirmar el origen real del frontend.

---

### H-API-09 — Errores devuelven `str(exception)` (Vulnerabilidad, media)

- **Hallazgo:** H-API-09. Evidencia: `api/app/main.py:26`, `api/app/main.py:120`, `api/app/main.py:121`.
- **Problema:** el 401 incluye `"Invalid token: " + str(error)` y `backend-health` devuelve `str(error)` en `body`, filtrando detalles de decodificación, host/puerto o errores de red. `docs/GOOD_PRACTICES.md`: `HTTPException` con mensajes genéricos, nunca `str(exception)` en la respuesta.
- **Cambio propuesto:**
  - Token: `HTTPException(status_code=401, detail="Invalid token")` (constante `INVALID_TOKEN_DETAIL`), registrando el motivo con `logging` en el servidor (`logger.warning(..., exc_info=...)` sin imprimir el token).
  - Salud: ante fallo conservar `status: 0` y `requestedBy`, con `body` genérico (constante `AUTH_UNAVAILABLE_MESSAGE`) y detalle solo en `logger.exception`/`warning`.
  - Un único helper para el log y para la construcción del 401 evita duplicar el `raise`.
- **Archivos a tocar:** `app/security.py` (coordinar con H-API-01, que reemplazará la lógica), `app/routes/health.py` o `app/services.py`, `app/config.py`; tests.
- **Prueba de caracterización previa:** `test_invalid_token_response_shape` (401 y `detail` actual con prefijo `Invalid token`) y `test_backend_health_failure_shape` (con URL inalcanzable o `monkeypatch` que lance excepción: 200, `status == 0`, claves `requestedBy/status/body`). Tras el cambio, las pruebas afirman que `detail` y `body` no contienen texto de la excepción.
- **Cambio de contrato:** el texto de `detail` y de `body` cambia (status y claves no). Requiere aprobación; ningún consumidor visto en `api/` depende del texto.

---

### H-API-10 — Sin validación de campos de tarea (Bug, baja) — Requiere decisión

- **Hallazgo:** H-API-10. Evidencia: `api/app/main.py:79`, `api/app/main.py:81`, `api/app/main.py:82`.
- **Problema:** `status`, `priority` y `title` aceptan cualquier texto o vacío; datos inconsistentes distorsionan `summary`.
- **Cambio propuesto:** `TaskCreate` (Pydantic) con `title: str` mínimo 1 y máximo acotado, `description: str = ""`, `status` con valores permitidos `TODO`, `IN_PROGRESS`, `DONE`, `ARCHIVED`, `priority` con `HIGH`, `MEDIUM`, `LOW` y defaults `TODO` / `MEDIUM`. Los valores salen de los datos semilla y de las reglas de `summary` (`api/app/main.py:40-42`, `api/app/main.py:101-103`), no de un contrato documentado, por lo que se confirman antes de aplicar. `owner` se conserva como campo opcional sin cambiar su semántica; la autorización por identidad pertenece a H-API-02. Campos extra siguen ignorándose (igual que hoy con `.get`).
- **Archivos a tocar:** `app/schemas.py`, `app/config.py` (enums/constantes), `app/routes/tasks.py`; tests.
- **Prueba de caracterización previa:** `test_create_task_accepts_arbitrary_values_today` (documenta el comportamiento actual: título vacío, status/priority arbitrarios → 201; valor numérico en `title` se convierte a texto por `str()`). Tras el cambio, esa prueba se reemplaza por pruebas de 422 y por una de payload válido con defaults.
- **Cambio de contrato:** sí (422 en vez de 201 para datos inválidos; los números dejan de coercionarse a texto). Alternativa conservadora si no se aprueba: aceptar cualquier `status`/`priority` y solo validar tipo y longitud. Requiere aprobación humana y revisar que `web` envíe los valores listados.

---

### H-API-11 — Ciclo de vida y recursos (Sugerencia, baja) — Requiere decisión parcial

- **Hallazgo:** H-API-11. Evidencia: `api/app/main.py:130`, `api/app/main.py:123`, `api/app/main.py:118`, `api/app/main.py:35`.
- **Problema:** `app = create_app()` crea BD y directorios al importar el módulo; `@app.on_event("shutdown")` está obsoleto; se crea un `PoolManager` por petición; una sola conexión SQLite con `check_same_thread=False` se comparte entre hilos sin sincronización. Estos puntos no están en `docs/GOOD_PRACTICES.md`; se tratan como mejora acotada.
- **Cambio propuesto:**
  - Reemplazar `on_event("shutdown")` por un `lifespan` que cierre el repositorio (no cambia comportamiento observable).
  - Un `urllib3.PoolManager` único guardado en `app.state` y reutilizado; `timeout` como constante.
  - Proteger el acceso a la conexión en el repositorio con `threading.Lock` (se mantiene una conexión; no se agregan dependencias).
  - Mantener `app = create_app()` en el módulo porque el arranque actual (Dockerfile / `tools/lab.py`) lo usa; cambiar a `--factory` exigiría tocar archivos fuera del alcance de `api/`, así que queda como riesgo pendiente y se coordina por separado.
- **Archivos a tocar:** `app/main.py`, `app/repository.py`, `app/routes/health.py` o `app/services.py`; tests.
- **Prueba de caracterización previa:** `test_connection_closed_on_shutdown` (tras salir del `with TestClient(app)`, `app.state.connection` ya no acepta consultas: `sqlite3.ProgrammingError`) y `test_concurrent_requests_do_not_fail` (varias peticiones concurrentes a `/api/tasks` con `ThreadPoolExecutor`, todas 200). Deben pasar antes y después.

---

### Riesgos pendientes y coordinación

- Decisiones que requieren aprobación humana: CORS (H-API-08), mensajes de error (H-API-09), validación (H-API-10), alcance del ciclo de vida (H-API-11) y versiones de dependencias (H-API-06). No hay aprobaciones registradas.
- Dependencias entre hallazgos: H-API-05/07/09 tocan `legacy_identity` y las consultas, que también cambian H-API-01 a H-API-04; hay que acordar el orden para evitar conflictos.
- Contrato acordado: `docs/ENDPOINTS.md` no existe; mientras tanto el contrato es el observado. Los cambios de H-API-08, H-API-09 y H-API-10 pueden afectar a `web` y no se pueden verificar desde `api/`.
- Cobertura: ver "Registro de ejecuciones" más abajo.

### Registro de ejecuciones (api, 2026-11-02)

Todas con cwd `api/` y `api/.venv` (Python 3.13.15), salvo la última, que usa el comando oficial desde la raíz.

| # | IDs | Comando | Resultado |
|---|---|---|---|
| 1 | línea base | `pytest --cov=app` | 4 passed; `app/main.py` 90% |
| 2 | H-API-05 a H-API-11 | `pytest tests` (caracterización, antes del cambio) | 17 passed (4 previas + 13 nuevas) |
| 3 | H-API-05 a H-API-11 | `pytest tests/test_corrections.py` (antes del cambio) | 19 failed, 3 passed (las 3 describen comportamiento que se conserva) |
| 4 | H-API-06 | OSV (`api.osv.dev`) para `urllib3 2.5.0` y `python-multipart 0.0.21` | 6 y 7 avisos respectivamente; fix mínimo global 2.8.0 y 0.0.31 |
| 5 | H-API-06 | pip install de las versiones nuevas, `pip check`, pruebas de caracterización + `h_api_06`; OSV de las versiones nuevas | sin dependencias rotas; 19 passed; OSV sin avisos |
| 6 | H-API-05, 06, 07 | `pytest tests` tras el refactor de capas | 28 passed, 11 failed (solo H-API-08 a H-API-11, aún sin implementar) |
| 7 | H-API-08 a H-API-11 | `pytest tests --cov=app` | 39 passed; cobertura 99% (`security.py:31` sin cubrir) |
| 8 | todos | `python tools/lab.py test api` (pytest `--cov=app --cov-fail-under=85`) | 43 passed; cobertura 100% (269 sentencias, 0 sin cubrir; 10 ramas, 0 parciales); informe en `api/htmlcov/index.html` |
| 9 | H-API-05 a H-API-11 (revisión) | OSV `querybatch` sobre los 31 paquetes instalados; sondeos locales con `TestClient` y datos ficticios | Avisos solo en `starlette 0.50.0` y `pytest 9.0.2`; confirma H-API-01 a H-API-04 aún explotables; alta de H-API-12 |
| 10 | documentación de `docs/ENDPOINTS.md` (todos los endpoints de api) | Capturas con `TestClient` sobre BD temporal y un servidor HTTP local de pruebas para `AUTH_HEALTH_URL`; sin cambios de código | Los ejemplos de respuesta y los códigos 200/201/401/404/405/422/500 del documento salen de esas ejecuciones |
| 11 | endpoints de api; H-API-02, 03, 04 (`xfail`) | `python tools/lab.py test api` (raíz, salida 0) y `python -m pytest tests/test_endpoints.py` (cwd `api/`, salida 0) | 134 passed, 6 xfailed; `test_endpoints.py` 91 passed, 6 xfailed; cobertura 100% (269/269 sentencias, 10/10 ramas). Detalle en `docs/TESTING.md` |

Cobertura del código modificado: numerador 269, denominador 269 (sentencias de `api/app/`, todo el paquete cambió) con `pytest-cov` y ramas activadas. Es la métrica de la app completa, que aquí coincide con la del diff porque todos los módulos de `app/` son nuevos o modificados.

### Desviaciones respecto al plan

- **Orden:** las pruebas de caracterización y de corrección se escribieron para todos los IDs antes de empezar, y los cambios se aplicaron en el orden 06 → 07+05 → 09 → 10 → 08 → 11, con ejecución de pruebas tras H-API-06, tras H-API-05/07 y al final; no hay ejecución intermedia tras H-API-09, H-API-10 y H-API-08 por separado.
- **Pruebas de caracterización reemplazadas:** como anticipaba el plan, `h_api_08` (CORS actual) y `h_api_10` (valores arbitrarios aceptados) se sustituyeron por su comportamiento nuevo; se añadió caracterización de ramas del token (formato, secreto, expiración, número) para cobertura.
- **H-API-05:** además de lo previsto se creó `app/dependencies.py` (acceso a servicios por `Request`) y `RequirementService` / `BackendHealthService` en `services.py`.
- **H-API-10:** los máximos `title` 200 y `description` 2000 son valores propuestos por mí (el plan decía "máximo acotado"); `owner` conserva su comportamiento y un `null` explícito en un campo opcional pasa a 422.
- **Sin cambios de SQL:** la concatenación se movió tal cual a `repository.py` (H-API-03 fuera del alcance aprobado).
- **Fuera de `api/`:** no se tocó `compose.yaml` ni `tools/`; `app.main:app` sigue existiendo.
