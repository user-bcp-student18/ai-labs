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

## Discovery: auth (candidatos, pendientes de revisión humana)

Alcance: `auth/` (Quarkus). Solo lectura; no se modificó código ni se crearon issues.
Contrato observado de `POST /auth/login`: entrada `username`, `password`, `client`; 200 con
`token`, `expiresIn`, `user{username,displayName,role}` y `debug`; 400/401/500 con `message`
(`auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:24-60`). `docs/ENDPOINTS.md`
no documenta `auth` todavía. Única prueba existente: login feliz
(`auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java:13-21`).

### H-AUTH-01 — Consulta de login con SQL concatenado
- Estado: CANDIDATO
- Evidencia: `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:32` arma `... WHERE username='" + username + "' AND password='" + password + "'"` con valores de `LoginRequest` (`AuthResource.java:35`) y la ejecuta con `Statement` (`LegacyDatabase.java:34`).
- Impacto: la entrada del cliente puede alterar la consulta de autenticación (omitir la validación de credenciales o provocar errores de BD).
- Prioridad propuesta: Alta
- Contrato potencialmente afectado: ninguno externo si se usa `PreparedStatement`; el 401 para credenciales inválidas debe conservarse.
- Cómo validarlo: prueba de caracterización con datos ficticios (usuario con apóstrofe y una condición siempre verdadera en `username`; esperar 401 tras la corrección) y `python tools/lab.py test auth`; revisión de `LegacyDatabase.java:32`.

### H-AUTH-02 — Contraseñas almacenadas y comparadas en texto plano
- Estado: CANDIDATO
- Evidencia: columna `password TEXT NOT NULL` (`LegacyDatabase.java:22`); semillas `'Workshop123!'` y `'Trainer123!'` insertadas tal cual (`LegacyDatabase.java:23`, `LegacyDatabase.java:24`); la comparación es igualdad directa en SQL (`LegacyDatabase.java:32`).
- Impacto: una lectura de `data/workshop.db` expone todas las credenciales; no hay salt ni costo de derivación.
- Prioridad propuesta: Alta
- Contrato potencialmente afectado: `POST /auth/login` debe seguir aceptando `student` / `trainer` con sus credenciales de prueba; requiere decidir la migración de usuarios existentes y la dependencia de hash (BCrypt/Argon2 y su justificación).
- Cómo validarlo: caracterizar el login de `student`; tras el cambio, verificar que la columna no contenga la contraseña en claro (consulta sobre una BD de prueba aislada) y que login válido/ inválido mantenga 200/401.

### H-AUTH-03 — Token Base64 sin firma que además incluye el secreto
- Estado: CANDIDATO
- Evidencia: `auth/src/main/java/com/bcp/workshop/auth/LegacyTokenUtil.java:8` (`SECRET` constante en código), `LegacyTokenUtil.java:14` (`username|role|expiry|SECRET`), `LegacyTokenUtil.java:15` (solo Base64); expiración fija `plusSeconds(3600)` (`LegacyTokenUtil.java:13`) y `expiresIn` fijo `3600` (`AuthResource.java:42`). `HALLAZGOS.md` ya registra que `api` valida este formato (H-API-01).
- Impacto: Base64 no es cifrado ni firma; cualquiera que reciba un token obtiene el secreto y puede fabricar tokens con otro usuario o rol. El secreto está versionado en el repositorio.
- Prioridad propuesta: Alta
- Contrato potencialmente afectado: formato del campo `token` consumido por `api` (y posiblemente `web`); cambiarlo exige coordinar con esos componentes (fuera del alcance de auth) y externalizar el secreto/clave a variable de entorno.
- Cómo validarlo: decodificar un token obtenido con credenciales de prueba y comprobar que el 4.º campo es el secreto (`python -c` local); prueba unitaria de `LegacyTokenUtil.create` y, tras el cambio, de firma/expiración/claims; confirmar con `api` y `web` el formato esperado antes de cambiarlo.

### H-AUTH-04 — Respuestas exponen detalles internos y datos de depuración
- Estado: CANDIDATO
- Evidencia: el 500 devuelve `error.getMessage()` y `error.getClass().getName()` (`AuthResource.java:54-58`); el 401 refleja el `username` enviado (`AuthResource.java:37`); el 200 incluye `"debug": "authenticated-with-legacy-flow"` (`AuthResource.java:48`); `LegacyDatabase` captura `Exception`, usa `printStackTrace()` y devuelve `null`, por lo que un fallo de BD se ve como credenciales inválidas (`LegacyDatabase.java:39-42`).
- Impacto: filtración de clases/mensajes internos, reflejo de entrada del usuario en la respuesta y diagnóstico poco fiable (error de infraestructura confundido con 401); sin logging controlado.
- Prioridad propuesta: Media
- Contrato potencialmente afectado: forma de `message`/`exception` en 500 y campo `debug` del 200; confirmar si `web` los consume antes de retirarlos.
- Cómo validarlo: forzar un error con `AUTH_DB_URL` inválido en un entorno de prueba y revisar el cuerpo del 500/401; `grep -r "debug\|exception" web/src` (solo lectura, en el paso de coordinación) para ver si algún consumidor depende de ellos.

### H-AUTH-05 — Dependencia `commons-text 1.9` con advisory conocido y CORS/config hardcodeados
- Estado: CANDIDATO
- Evidencia: `auth/pom.xml:49-50` fija `commons-text` `1.9`; consulta a OSV (2026-11-03, `POST https://api.osv.dev/v1/query` con `org.apache.commons:commons-text@1.9`) devolvió GHSA-599f-7c49-w659 / CVE-2022-42889. El código solo usa `StringEscapeUtils.escapeHtml4` (`AuthResource.java:10`, `AuthResource.java:45`), por lo que la alcanzabilidad parece baja (no confirmada). Configuración fija: `quarkus.http.cors.origins=/.*/` y puerto/host en `auth/src/main/resources/application.properties:1-5`. Quarkus `3.27.4` (`pom.xml:13`) no fue consultado.
- Impacto: riesgo de cadena de suministro y CORS abierto a cualquier origen; la dependencia es removible si el escape no es necesario (JSON ya se serializa).
- Prioridad propuesta: Media
- Contrato potencialmente afectado: `user.displayName` se devuelve escapado con `escapeHtml4`; eliminar/actualizar la librería cambia el valor de ese campo si contiene `<>&"'`. CORS: orígenes del frontend por entorno.
- Cómo validarlo: repetir la consulta OSV (también para Quarkus 3.27.4) o `mvn dependency:tree` desde `auth/`; verificar con una prueba que `displayName` mantiene su formato; `OPTIONS /auth/login` con un `Origin` no autorizado antes y después.

Observaciones no promovidas (sin evidencia suficiente de impacto propio): cobertura de pruebas limitada a un caso (meta JaCoCo 85 %), `AuthResource.login` mezcla validación, acceso a datos y respuesta con anidamiento profundo (`AuthResource.java:26-53`) y `3600` duplicado como valor mágico (`LegacyTokenUtil.java:13`, `AuthResource.java:42`). Se tratarán como soporte de los candidatos anteriores si se aprueban.

**Detenido para revisión humana.** No se crearon issues; ningún candidato está confirmado.

## Discovery: api (candidatos, pendientes de revisión humana)

Alcance: `api/` (FastAPI), código actual de la rama `main` ya refactorizado (H-API-05 a H-API-11). Solo lectura; no se modificó código ni se crearon issues. Los IDs continúan la numeración existente (H-API-13 a H-API-16) y no se renumeró nada. No repiten H-API-01 a H-API-04 ni H-API-12, que siguen "Pendiente" en la matriz. Contrato de referencia: `docs/ENDPOINTS.md` (sección api; contrato observado, no acordado con consumidores).

Los comportamientos de H-API-14, H-API-15 y H-API-16 se comprobaron con un script local de solo lectura (`TestClient` de FastAPI sobre BD y directorio temporales, usuarios ficticios `alice`/`bob`, token armado con el secreto del propio código). No se escribió nada en el repositorio. Las pruebas automatizadas no se ejecutaron en este paso.

### H-API-13 — La imagen del contenedor ejecuta la API como root
- Estado: CANDIDATO
- Evidencia: `api/Dockerfile:1-9` no declara `USER`; `RUN mkdir -p /data /uploads` (`api/Dockerfile:7`) y `CMD ["uvicorn", ...]` (`api/Dockerfile:9`) corren como root. `compose.yaml` monta los volúmenes `api-data:/data` y `api-uploads:/uploads` en ese contenedor. `docs/GOOD_PRACTICES.md` y `docs/ENDPOINTS.md` no mencionan el usuario del contenedor.
- Impacto: cualquier escritura de la API ocurre con privilegios de root dentro del contenedor. Amplifica H-API-04 (escritura fuera de `uploads/` con `../`) y cualquier fallo futuro de ejecución de código. No es una vulnerabilidad por sí sola.
- Prioridad propuesta: Media
- Contrato potencialmente afectado: ninguno HTTP. Operativo: propiedad y permisos de los volúmenes `/data` y `/uploads` (una BD y archivos ya creados por root dejarían de ser escribibles si se cambia de usuario sin `chown`).
- Cómo validarlo: `docker compose build api` y `docker compose run --rm --entrypoint id api` (debería mostrar `uid=0` hoy); tras un cambio, `docker compose up api` + `POST /api/tasks` y `POST /api/requirements` con datos ficticios, y revisar CodeQL/escáner de imágenes si existe. No se ejecutó Docker en este discovery; la evidencia es la lectura del Dockerfile.

### H-API-14 — `owner` vacío en `POST /api/tasks` crea tareas inalcanzables por la API
- Estado: CANDIDATO
- Evidencia: `TaskService.create_task` usa `default_owner if payload.owner is None else payload.owner` (`api/app/services.py:38`), por lo que `""` es aceptado como `owner` (`api/app/schemas.py:23`, sin `min_length`); en cambio `resolve_owner` usa `requested_owner or identity["username"]` (`api/app/services.py:23`), de modo que `?owner=` se trata como "no enviado". Comprobado localmente: `POST /api/tasks` con `"owner": ""` responde 201 con `owner: ""`; `GET /api/tasks?owner=` y `GET /api/tasks` devuelven `[]` para esa tarea (no se puede listar ni resumir por ninguna ruta).
- Impacto: dato huérfano y reglas inconsistentes entre creación y consulta de `owner`; filas con `owner` vacío ensucian la BD y no se pueden ver ni resumir.
- Prioridad propuesta: Baja
- Contrato potencialmente afectado: `POST /api/tasks` (campo `owner`, hoy opcional y libre) y `GET /api/tasks` / `GET /api/summary` (parámetro `owner`). Su solución depende de la decisión de H-API-02 (si `owner` deja de aceptarse del cliente, este caso desaparece); no cambiar antes de decidirla.
- Cómo validarlo: prueba de caracterización con `TestClient` (BD temporal): `POST` con `owner=""`, luego `GET ?owner=` y `GET` sin parámetro; esperar 422 o asignación al usuario del token según lo que se acuerde. `python tools/lab.py test api` para el resto de la suite.

### H-API-15 — Archivos subidos en un directorio plano compartido y sobrescribibles por cualquier usuario autenticado
- Estado: IMPLEMENTADO — pendiente de revisión humana (rama local `day1/prompting`; ver `PLAN.md`, sección "H-API-15", y `docs/TESTING.md`, ejecuciones 6 a 8). Antes: CANDIDATO.
- Evidencia: `RequirementService.store` calcula `self._upload_dir / str(filename)` y llama `write_bytes` (`api/app/services.py:57-58`) sin separar por usuario ni impedir que el archivo ya exista; la ruta (`api/app/routes/requirements.py:17-19`) devuelve 201 y `storedAt` con la ruta del servidor. Comprobado localmente: `alice` sube `req.txt` y `bob` sube otro `req.txt`; ambos reciben 201 y el contenido final es el de `bob`. Relacionado con H-API-04 (nombre/tamaño/extensión) pero distinto: ocurre con un nombre legítimo y dentro del directorio de cargas.
- Impacto: pérdida o sustitución silenciosa de archivos de otro usuario; `owner` de la respuesta no está ligado a lo almacenado. Una validación de nombre (H-API-04) no lo corrige por sí sola.
- Prioridad propuesta: Media
- Contrato potencialmente afectado: `POST /api/requirements` (201 con `owner`, `fileName`, `storedAt`, `size`; `storedAt` cambiaría si se usan subdirectorios o nombres únicos). Debe decidirse junto con H-API-04 y confirmar con `web` si usa `storedAt`.
- Cómo validarlo: prueba de caracterización con dos tokens ficticios y el mismo `fileName` (comparar el contenido final) y, tras el cambio, comprobar que ambos archivos coexisten y que `storedAt` sigue siendo coherente; `python tools/lab.py test api`. Revisar con el equipo si el espacio por usuario es el comportamiento deseado antes de implementarlo.

### H-API-16 — `GET /api/backend-health` puede retener un hilo mucho más del tiempo configurado y devuelve el cuerpo completo del servicio de auth
- Estado: CANDIDATO
- Evidencia: `BackendHealthService.check` llama `self._pool.request("GET", auth_health_url(), timeout=HEALTH_TIMEOUT_SECONDS)` (`api/app/services.py:68`; `HEALTH_TIMEOUT_SECONDS = 3.0` en `api/app/config.py:11`) con un `PoolManager()` sin política de reintentos (`api/app/main.py:19`), y el cuerpo se lee y se devuelve completo (`api/app/services.py:69`, `api/app/routes/health.py:16-17`). La ruta es síncrona (`def`, `api/app/routes/health.py:12`) y ocupa un hilo del pool de FastAPI. Comprobado localmente con un servidor que acepta conexiones y no responde: la llamada tardó 12,1 s (4 intentos de 3 s) y respondió 200 con `status: 0`; el log mostró "Max retries exceeded ... Read timed out".
- Impacto: un usuario autenticado puede mantener ocupados varios hilos durante ~12 s con peticiones repetidas si `auth` está lento; la latencia real cuadruplica el timeout documentado. El cuerpo sin límite de tamaño de un servicio caído o distinto se devuelve tal cual al cliente.
- Prioridad propuesta: Baja
- Contrato potencialmente afectado: `GET /api/backend-health` (200 con `requestedBy`, `status`, `body`; `status: 0` y mensaje genérico ante fallo, ya aprobado en H-API-09). Un cambio de reintentos solo altera el tiempo de respuesta ante fallo; limitar el cuerpo sí cambiaría `body`.
- Cómo validarlo: repetir la medición con un socket local que no responde (BD y directorios temporales) y comprobar que el tiempo máximo coincide con el timeout acordado; prueba de caracterización del mapeo a `status: 0`; confirmar con `web` si el cuerpo se muestra al usuario.

### Observaciones no promovidas (api)

- Las filas H-API-01 a H-API-04 de la matriz citan `api/app/main.py:NN` del commit `0e0b646`. En el código actual esos puntos están en `api/app/security.py:10`, `api/app/security.py:26-31` (token), `api/app/services.py:23` y `api/app/routes/tasks.py:17`, `api/app/routes/tasks.py:26`, `api/app/routes/tasks.py:35` (`owner`), `api/app/repository.py:50`, `api/app/repository.py:56-58`, `api/app/repository.py:71` (SQL concatenado) y `api/app/services.py:57` (nombre de archivo). Conviene actualizar las referencias cuando se aborden; no son un hallazgo nuevo.
- `summarize` carga todas las filas del `owner` y cuenta en Python (`api/app/services.py:42-48`, `api/app/repository.py:70-73`); sin evidencia de impacto con el volumen actual (3 filas semilla). `GET /api/tasks` no pagina. Se tratarán solo si el volumen real lo justifica.
- El `role` del token se extrae pero no se usa en ninguna ruta (`api/app/security.py:32`); ya cubierto por la pregunta abierta 4 de `docs/ENDPOINTS.md` y por H-API-02.

**Detenido para revisión humana.** No se crearon issues; ningún candidato de api está confirmado ni aprobado.