# Hallazgos

## Contrato observado: api

No existe `docs/ENDPOINTS.md`. El siguiente resumen describe únicamente lo
observable en `api/app/main.py`; no es un contrato acordado. Las rutas dependen
de `legacy_identity`, que extrae username y role de un token Base64 y devuelve
401 cuando ocurre una excepción (`api/app/main.py:17`,
`api/app/main.py:20`, `api/app/main.py:25`).

| Ruta | Comportamiento observado | Evidencia |
|---|---|---|
| `GET /api/tasks` | Acepta `owner` opcional; si no se envía, usa el username del token. Devuelve las tareas como lista. | `api/app/main.py:67`, `api/app/main.py:68`, `api/app/main.py:69`, `api/app/main.py:70` |
| `POST /api/tasks` | Acepta un objeto JSON; asigna valores por defecto a campos ausentes y responde 201 con la tarea creada. | `api/app/main.py:77`, `api/app/main.py:78`, `api/app/main.py:83`, `api/app/main.py:84` |
| `GET /api/summary` | Acepta `owner` opcional; si no se envía, usa el username del token. Devuelve total, conteo por estado y tareas abiertas de prioridad alta. | `api/app/main.py:90`, `api/app/main.py:91`, `api/app/main.py:92`, `api/app/main.py:94` |
| `POST /api/requirements` | Recibe un archivo, lo escribe en el directorio configurado y responde 201 con nombre, ruta y tamaño. | `api/app/main.py:107`, `api/app/main.py:108`, `api/app/main.py:109`, `api/app/main.py:111` |
| `GET /api/backend-health` | Consulta la URL `AUTH_HEALTH_URL` (por defecto, localhost) y devuelve estado y cuerpo; ante excepción, devuelve estado 0 y el detalle de la excepción. | `api/app/main.py:114`, `api/app/main.py:115`, `api/app/main.py:116`, `api/app/main.py:120` |

La conexión SQLite y la tabla `tasks` se crean durante `create_app`; las rutas
leen y escriben usando esa conexión (`api/app/main.py:29`,
`api/app/main.py:35`, `api/app/main.py:36`).

### Flujo del token, SQLite y archivos (api, observado)

- Token: `Authorization` se lee con valor por defecto vacío y se quita `Bearer ` con `replace` (`api/app/main.py:17`, `api/app/main.py:19`); se decodifica Base64 y se divide por `|` en `username|role|expiración|secreto` (`api/app/main.py:20`, `api/app/main.py:21`); solo se compara el 4.º campo con `LEGACY_SECRET` y se revisa la expiración (`api/app/main.py:14`, `api/app/main.py:22`). Devuelve `username` y `role` (`api/app/main.py:24`); `role` no se usa en ninguna ruta. Todo error se vuelve 401 con `str(error)` (`api/app/main.py:25`, `api/app/main.py:26`).
- SQLite: una única conexión compartida con `check_same_thread=False`, esquema y datos semilla creados dentro de `create_app` y cierre en `shutdown` (`api/app/main.py:35`, `api/app/main.py:37`, `api/app/main.py:40`, `api/app/main.py:123`). Tres rutas construyen SQL por concatenación (`api/app/main.py:70`, `api/app/main.py:84`, `api/app/main.py:93`).
- Archivos: directorio `WORKSHOP_UPLOAD_DIR` (por defecto `./uploads`) (`api/app/main.py:31`); el destino es directorio + `file.filename`, se lee todo en memoria y se escribe con `write_bytes`; la respuesta devuelve `storedAt` con la ruta del servidor (`api/app/main.py:109`, `api/app/main.py:110`, `api/app/main.py:111`, `api/app/main.py:112`).

## Matriz de seguimiento

| id | componente | hallazgo | tipo | explicacion | evidencia (archivo:linea) | severidad | estado |
|---|---|---|---|---|---|---|---|
| H-API-01 | api | Token Base64 con secreto embebido y sin firma criptográfica | Vulnerabilidad | La validación decodifica el contenido y compara un secreto hardcodeado; no verifica una firma. Si el secreto incluido en el código se conoce, se puede fabricar un token con identidad arbitraria, afectando la autenticación. La expiración sí se comprueba. | `api/app/main.py:14`, `api/app/main.py:20`, `api/app/main.py:22` | alta | Pendiente |
| H-API-02 | api | El cliente puede consultar o asignar otro `owner` | Vulnerabilidad | `GET /api/tasks` y `GET /api/summary` aceptan un `owner` enviado por el cliente; `POST /api/tasks` también permite definirlo en el JSON. No se fuerza que coincida con la identidad del token, lo que permite acceso o atribución entre usuarios. | `api/app/main.py:68`, `api/app/main.py:69`, `api/app/main.py:78`, `api/app/main.py:83`, `api/app/main.py:91`, `api/app/main.py:92` | alta | Pendiente |
| H-API-03 | api | Filtros e inserts SQL concatenan valores de entrada | Vulnerabilidad | Los valores `owner`, `title`, `description`, `status`, `priority` y `owner` se interpolan en consultas SQL. Comillas o contenido especialmente formado pueden alterar la consulta, provocar errores o modificar su significado. | `api/app/main.py:70`, `api/app/main.py:84`, `api/app/main.py:93` | alta | Pendiente |
| H-API-04 | api | Carga de archivos usa directamente `upload.filename` y lee el archivo completo | Vulnerabilidad | El nombre se combina con el directorio de destino sin normalización visible, y el contenido se lee completo sin límite visible. Un nombre relativo puede intentar salir del directorio de cargas y archivos grandes pueden consumir memoria; no se observa validación de extensión o tamaño. | `api/app/main.py:108`, `api/app/main.py:109`, `api/app/main.py:110`, `api/app/main.py:111` | media | Pendiente |
| H-API-05 | api | Rutas, SQLite, reglas y serialización están concentradas en un módulo | Refactor | `create_app` inicializa la base y declara las rutas; estas consultan SQLite, aplican reglas y forman respuestas en el mismo archivo. Esto dificulta aislar responsabilidades y probarlas sin acoplamiento. | `api/app/main.py:29`, `api/app/main.py:35`, `api/app/main.py:56`, `api/app/main.py:67`, `api/app/main.py:77`, `api/app/main.py:90`, `api/app/main.py:107` | media | Resuelto — `main.py` solo cablea la app; SQL en `repository.py`, reglas en `services.py`, rutas delgadas en `routes/` (sin SQL), modelos en `schemas.py`, constantes en `config.py`. |
| H-API-08 | api | CORS abierto con credenciales (adicional, no listado en `RETO.md`) | Vulnerabilidad | `allow_origins=["*"]` junto con `allow_credentials=True` y métodos y cabeceras abiertos permite que cualquier origen interactúe con la API desde un navegador; debe restringirse por entorno. | `api/app/main.py:48`, `api/app/main.py:50`, `api/app/main.py:51` | media | Resuelto — orígenes por `WORKSHOP_CORS_ORIGINS` (por defecto `http://localhost:4200`), métodos GET/POST y cabeceras Authorization/Content-Type. Pendiente confirmar el origen real del frontend. |
| H-API-09 | api | Errores devuelven `str(exception)` al cliente (adicional, contemplado en `docs/GOOD_PRACTICES.md`) | Vulnerabilidad | El 401 y `backend-health` incluyen el texto de la excepción, que puede revelar detalles de decodificación, URL o red interna y facilita el reconocimiento del sistema. | `api/app/main.py:26`, `api/app/main.py:120`, `api/app/main.py:121` | media | Resuelto — 401 con `detail: "Invalid token"` y salud con `body: "Auth service unavailable"`; el detalle va a `logging` del servidor. |
| H-API-12 | api | Dependencia transitiva `starlette 0.50.0` (vía `fastapi==0.128.2`) con avisos conocidos (adicional, detectado en revisión) | Vulnerabilidad | OSV reporta 5 GHSA para `starlette 0.50.0` (p. ej. GHSA-86qp-5c8j-p5mr Host sin validar, GHSA-82w8-qh3p-5jfq límites de `request.form()` ignorados, GHSA-x746-7m8f-x49c, GHSA-wqp7-x3pw-xc5r, GHSA-jp82-jpqv-5vv3) con correcciones en 1.0.1 a 1.3.1. En `api/app/` no se usan `StaticFiles` ni `HTTPEndpoint`, por lo que la alcanzabilidad parece baja; no está confirmada. Corregirlo exige subir `fastapi` y revisar compatibilidad. | `api/requirements.txt:1` | media | Pendiente |
| H-API-06 | api | Dependencias `urllib3` 2.5.0 y `python-multipart` 0.0.21 requieren evaluación de advisories | Sugerencia | Las versiones coinciden con las señaladas en `RETO.md`, pero esta inspección no consultó advisories ni confirma que sean vulnerables. Se necesita una evaluación de dependencias antes de afirmar un CVE o proponer una actualización. | `api/requirements.txt:4`, `api/requirements.txt:5` | baja | Resuelto — OSV confirmó avisos en `urllib3 2.5.0` (fix hasta 2.8.0) y `python-multipart 0.0.21` (fix hasta 0.0.31); fijadas `urllib3==2.8.0` y `python-multipart==0.0.31`; OSV sin avisos para esas versiones y `pip check` limpio. |
| H-API-07 | api | Uso de `dict`/`Any`, captura amplia de excepciones y lógica anidada | Refactor | Los tipos poco específicos reducen la validación del contrato; capturar `Exception` puede ocultar causas distintas; y el anidamiento en el resumen dificulta seguir la lógica y mantenerla. | `api/app/main.py:17`, `api/app/main.py:25`, `api/app/main.py:56`, `api/app/main.py:78`, `api/app/main.py:94`, `api/app/main.py:101`, `api/app/main.py:102`, `api/app/main.py:103` | baja | Resuelto — modelos Pydantic de request/response con alias camelCase, `Counter` y `is_high_priority_open` sin anidamiento, constantes con nombre, `except ValueError` y `except (HTTPError, UnicodeDecodeError)`. |
| H-API-10 | api | Sin validación de campos de tarea (adicional) | Bug | `status` y `priority` aceptan cualquier texto y `title` puede quedar vacío (valor por defecto `""`); datos inconsistentes distorsionan los conteos de `summary`. | `api/app/main.py:79`, `api/app/main.py:81`, `api/app/main.py:82` | baja | Resuelto — `TaskCreate` exige `title` (1–200), `status` y `priority` como enums y `description` ≤ 2000; datos inválidos responden 422. |
| H-API-11 | api | Ciclo de vida y recursos (adicional) | Sugerencia | `app = create_app()` crea BD y directorios al importar el módulo; `on_event("shutdown")` está obsoleto en FastAPI (usar `lifespan`); se crea un `PoolManager` por petición; la conexión SQLite única se comparte entre hilos. | `api/app/main.py:130`, `api/app/main.py:123`, `api/app/main.py:118`, `api/app/main.py:35` | baja | Resuelto — `lifespan` cierra repositorio y pool, un único `PoolManager` compartido y `RLock` sobre la conexión SQLite. `app = create_app()` se mantiene a nivel de módulo por el arranque actual. |

Nota de orden: los IDs existentes no se renumeraron. H-API-08 y H-API-09 (media) se ubican antes de H-API-06 para mantener el orden por severidad.

### Cobertura de `RETO.md` (api)

| Caso de RETO.md | Estado en el código | Fila |
|---|---|---|
| SCA (`urllib3 2.5.0`, `python-multipart 0.0.21`) | Versiones presentes; CVE sin confirmar | H-API-06 |
| Auth (token Base64 con secreto) | Presente | H-API-01 |
| Autorización (`owner` del cliente) | Presente | H-API-02 |
| SQL (filtros e inserts concatenados) | Presente | H-API-03 |
| Files (`upload.filename`) | Presente | H-API-04 |
| Arquitectura (todo en un archivo) | Presente | H-API-05 |
| Calidad (`dict`, excepciones amplias, condicionales, duplicación) | Presente (la duplicación se ve en la consulta/serialización repetida y los literales `HIGH`/`DONE`/`ARCHIVED`: `api/app/main.py:70`, `api/app/main.py:93`, `api/app/main.py:101`, `api/app/main.py:102`, `api/app/main.py:103`) | H-API-07 |

Ningún caso de `RETO.md` (api) quedó como "No encontrado".

### Pendientes (api)

- H-API-06 resuelto con advisories de OSV (consulta del 2026-11-02); H-API-05 a H-API-11 resueltos. H-API-01 a H-API-04 siguen "Pendiente" y fuera del alcance aprobado.
- `repository.py` conserva el SQL concatenado de `owner` y de los INSERT tal como estaba (H-API-03 pendiente); H-API-10 reduce la entrada libre de `status` y `priority`, pero no sustituye la parametrización.
- `docs/ENDPOINTS.md` (creado el 2026-11-02) documenta el contrato observado; no hay contrato acordado con auth y web, incluido el formato del token. Cambios en token u `owner` requieren revisar los consumidores (auth y web) sin ampliar el alcance.
- Cambios de contrato aprobados por el usuario que no se pudieron verificar contra `web`: CORS (H-API-08), textos de error (H-API-09) y 422 en tareas inválidas (H-API-10).
- Revisión local del diff (2026-11-02, agente; la aprobación humana sigue pendiente): H-API-05 a H-API-11 verificados como "Resuelto" sin regresiones. Las líneas `api/app/main.py:NN` de las filas son del código en `main` (commit `0e0b646`); el código actual está repartido en `config.py`, `repository.py`, `services.py`, `security.py` y `routes/`.
- Ejecuciones registradas en PLAN.md (sección "Registro de ejecuciones"). Revisión humana del diff pendiente.
- Sondeos locales con datos ficticios (2026-11-02) confirmaron que H-API-01 a H-API-04 siguen explotables: `owner` ajeno devuelve tareas de otro usuario, una tautología en `owner` devuelve tareas de todos, un título con apóstrofe devuelve 500, `../escape.txt` escribe fuera de `uploads/` y un token fabricado con el secreto del código es aceptado.
- `api/tests/test_endpoints.py` (2026-11-02) añade 6 pruebas `xfail(strict=True)` que reproducen H-API-02, H-API-03 y H-API-04; las filas siguen "Pendiente". Detalle en `docs/TESTING.md`.