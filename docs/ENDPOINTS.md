# Endpoints de ReqFlow

Este archivo documenta los contratos HTTP por componente. Cada componente mantiene solo su sección.

## api

API FastAPI de tareas y requerimientos (`api/app/`). Documento creado el 2026-11-02 a partir del código actual de la rama de trabajo y de ejecuciones locales con datos ficticios (BD temporal, sin red externa). Los ejemplos de respuesta son salidas reales de esas ejecuciones.

### Cómo leer este documento

- **Contrato observado:** lo que el código actual hace hoy y está descrito en las secciones de cada endpoint.
- **Contrato acordado:** no existía un documento previo. El único acuerdo registrado son los cambios aprobados por el usuario en `PLAN.md` (ver "Cambios respecto al comportamiento original"). No hay aprobación de un consumidor (`web`, `auth`) sobre este contrato.
- **Riesgos pendientes:** ver "Riesgos de seguridad pendientes" y "Preguntas abiertas". Algunas notas de seguridad describen limitaciones actuales, no garantías.

### Información común

**URL base:** `http://localhost:8000` (puerto indicado en `README.md`). Documentación interactiva generada por FastAPI: `/docs`.

**Formato:** salvo `POST /api/requirements` (`multipart/form-data`), las peticiones y respuestas usan `application/json`. Los nombres JSON de las respuestas están en camelCase (`createdAt`, `byStatus`, `highPriorityOpen`, `fileName`, `storedAt`, `requestedBy`).

**Autenticación (todos los endpoints):** cabecera `Authorization: Bearer <token>`.

| Aspecto                      | Comportamiento observado (`api/app/security.py`)                                                                                                                               |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Formato del token            | Base64 (UTF-8) del texto `usuario\|rol\|expiracion\|secreto`, con `expiracion` en segundos Unix. El valor del secreto lo conoce el servidor y no se documenta aquí.            |
| Qué se valida               | Que haya 4 campos separados por `\|`, que el cuarto coincida con el secreto del servidor y que la expiración no haya pasado. No hay firma criptográfica, emisor ni audiencia. |
| Identidad que se usa         | El campo `usuario` (`username`). El campo `rol` se lee pero ningún endpoint lo usa.                                                                                       |
| Prefijo                      | Se elimina el texto `Bearer ` (con mayúscula inicial y un espacio). `bearer <token>` y `Token <token>` dan 401. Un token enviado sin prefijo también se acepta.          |
| Cabecera ausente o inválida | 401 (ver abajo).                                                                                                                                                                 |

El token lo emite el servicio de autenticación del proyecto; este documento no describe su emisión (ver preguntas abiertas).

**Errores comunes a todos los endpoints**

| Código | Cuándo ocurre                                                                                                                                                                                                                                                                                 | Cuerpo de ejemplo                    |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| 401     | Falta la cabecera `Authorization`, el token no es Base64/UTF-8 válido, no tiene 4 campos, el secreto no coincide, la expiración ya pasó o no es numérica. La autenticación se evalúa antes que la validación del cuerpo: una petición sin token y con cuerpo inválido responde 401. | `{"detail": "Invalid token"}`      |
| 404     | La ruta no existe.                                                                                                                                                                                                                                                                             | `{"detail": "Not Found"}`          |
| 405     | El método no está permitido para la ruta (p. ej. `DELETE /api/tasks`).                                                                                                                                                                                                                     | `{"detail": "Method Not Allowed"}` |
| 500     | Error interno no controlado. El cliente recibe un texto genérico, `Content-Type: text/plain`; el detalle solo se registra en el log del servidor.                                                                                                                                           | `Internal Server Error`            |

**CORS (`api/app/main.py`, `api/app/config.py`):** orígenes permitidos desde la variable de entorno `WORKSHOP_CORS_ORIGINS` (lista separada por comas; por defecto `http://localhost:4200`). Métodos permitidos: `GET`, `POST`. Cabeceras permitidas: `Authorization`, `Content-Type` (más las cabeceras simples de CORS). Se permiten credenciales. Un origen no listado no recibe cabeceras `access-control-allow-*`.

**Variables de entorno de la API:** `WORKSHOP_DB_PATH` (por defecto `./data/workshop.db`), `WORKSHOP_UPLOAD_DIR` (por defecto `./uploads`), `AUTH_HEALTH_URL` (por defecto `http://localhost:8080/q/health`), `WORKSHOP_CORS_ORIGINS`.

**Error de validación (422), formato común de FastAPI:** `detail` es una lista; cada elemento tiene `type`, `loc` (dónde falló), `msg`, `input` y, a veces, `ctx`.

---

### GET /api/tasks

**1. Qué hace:** devuelve la lista de tareas de un responsable (por defecto, el usuario autenticado), ordenadas por `id` ascendente.

**2. Autenticación:** sí. Cabecera `Authorization: Bearer <token>`.

**3. Request**

| Parámetro        | Ubicación | Tipo   | Obligatorio | Descripción                                                                                            |
| ----------------- | ---------- | ------ | ----------- | ------------------------------------------------------------------------------------------------------- |
| `Authorization` | cabecera   | string | sí         | `Bearer <token>`.                                                                                     |
| `owner`         | query      | string | no          | Responsable cuyas tareas se piden. Si se omite o es una cadena vacía, se usa el `usuario` del token. |

Ejemplo:

```http
GET /api/tasks HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token>
```

```http
GET /api/tasks?owner=trainer HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token>
```

**4. Respuesta exitosa: 200** (`application/json`, lista; `[]` si el responsable no tiene tareas)

| Campo           | Tipo   | Descripción                                                                                          |
| --------------- | ------ | ----------------------------------------------------------------------------------------------------- |
| `id`          | entero | Identificador autoincremental.                                                                        |
| `title`       | string | Título.                                                                                              |
| `description` | string | Descripción (puede ser `""`).                                                                      |
| `status`      | string | Estado. Las tareas creadas por la API usan `TODO`, `IN_PROGRESS`, `DONE` o `ARCHIVED`.        |
| `owner`       | string | Responsable de la tarea.                                                                              |
| `priority`    | string | Prioridad. Las tareas creadas por la API usan `HIGH`, `MEDIUM` o `LOW`.                         |
| `createdAt`   | string | Fecha de creación, formato `AAAA-MM-DD HH:MM:SS` generado con `datetime('now')` de SQLite (UTC). |

```json
[
  {"id": 1, "title": "Refactor login", "description": "Separar responsabilidades en frontend", "status": "TODO", "owner": "student", "priority": "HIGH", "createdAt": "2026-11-02 22:13:25"},
  {"id": 2, "title": "Review API", "description": "Revisar seguridad de endpoints", "status": "IN_PROGRESS", "owner": "student", "priority": "MEDIUM", "createdAt": "2026-11-02 22:13:25"}
]
```

(Los datos semilla de una BD nueva son 2 tareas de `student` y 1 de `trainer`.)

**5. Errores**

| Código | Cuándo                                                                                  | Cuerpo de ejemplo               |
| ------- | ---------------------------------------------------------------------------------------- | ------------------------------- |
| 401     | Token ausente o inválido.                                                               | `{"detail": "Invalid token"}` |
| 500     | `owner` contiene una comilla simple (por ejemplo `O'Brien`). Ver riesgos pendientes. | `Internal Server Error`       |

**6. Notas de seguridad**

- **La autorización NO está ligada a la identidad del token:** cualquier usuario autenticado puede pedir las tareas de otro enviando `owner` (hallazgo H-API-02, pendiente). Los clientes no deben considerar `owner` como un control de acceso.
- `owner` se concatena en la consulta SQL (hallazgo H-API-03, pendiente): además del 500 anterior, el valor puede alterar la consulta. No usar entrada no confiable en `owner`.

---

### POST /api/tasks

**1. Qué hace:** crea una tarea nueva para el usuario autenticado (o para el `owner` indicado) y devuelve la tarea creada.

**2. Autenticación:** sí. Cabecera `Authorization: Bearer <token>`.

**3. Request** (`Content-Type: application/json`)

| Campo           | Tipo          | Obligatorio | Descripción                                                                                            |
| --------------- | ------------- | ----------- | ------------------------------------------------------------------------------------------------------- |
| `title`       | string        | sí         | Título; de 1 a 200 caracteres.                                                                         |
| `description` | string        | no          | Descripción; hasta 2000 caracteres. Por defecto `""`.                                                |
| `status`      | string (enum) | no          | `TODO`, `IN_PROGRESS`, `DONE` o `ARCHIVED`. Por defecto `TODO`.                               |
| `priority`    | string (enum) | no          | `HIGH`, `MEDIUM` o `LOW`. Por defecto `MEDIUM`.                                                 |
| `owner`       | string        | no          | Responsable. Si se omite, se usa el `usuario` del token. Se acepta cualquier cadena, incluida `""`. |

Los campos desconocidos se ignoran. Los números en lugar de texto (por ejemplo `"title": 123`) se rechazan con 422.

```http
POST /api/tasks HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token>
Content-Type: application/json

{"title": "Escribir pruebas", "description": "Cubrir login", "status": "IN_PROGRESS", "priority": "HIGH"}
```

**4. Respuesta exitosa: 201** (`application/json`)

| Campo           | Tipo   | Descripción                                       |
| --------------- | ------ | -------------------------------------------------- |
| `id`          | entero | Identificador asignado.                            |
| `title`       | string | Título guardado.                                  |
| `description` | string | Descripción guardada.                             |
| `status`      | string | Estado guardado.                                   |
| `owner`       | string | Responsable guardado.                              |
| `priority`    | string | Prioridad guardada.                                |
| `createdAt`   | string | Fecha de creación (`AAAA-MM-DD HH:MM:SS`, UTC). |

```json
{"id": 4, "title": "Escribir pruebas", "description": "Cubrir login", "status": "IN_PROGRESS", "owner": "student", "priority": "HIGH", "createdAt": "2026-11-02 22:13:25"}
```

Con solo `{"title": "Solo titulo"}` la respuesta es `{"id": 5, "title": "Solo titulo", "description": "", "status": "TODO", "owner": "student", "priority": "MEDIUM", "createdAt": "2026-11-02 22:13:25"}`.

**5. Errores**

| Código | Cuándo                                                                                                                                                                              | Cuerpo de ejemplo                                                                                                                                                                                                              |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 401     | Token ausente o inválido.                                                                                                                                                           | `{"detail": "Invalid token"}`                                                                                                                                                                                                |
| 422     | Falta `title`, está vacío o supera 200 caracteres, `description` supera 2000, `status` o `priority` fuera de los valores permitidos, tipos incorrectos o JSON mal formado. | `{"detail": [{"type": "missing", "loc": ["body", "title"], "msg": "Field required", "input": {}}]}`                                                                                                                          |
| 422     | `status` inválido.                                                                                                                                                                | `{"detail": [{"type": "enum", "loc": ["body", "status"], "msg": "Input should be 'TODO', 'IN_PROGRESS', 'DONE' or 'ARCHIVED'", "input": "LO-QUE-SEA", "ctx": {"expected": "'TODO', 'IN_PROGRESS', 'DONE' or 'ARCHIVED'"}}]}` |
| 500     | `title`, `description` u `owner` contienen una comilla simple (por ejemplo `it's`). Un título legítimo como `O'Brien` falla.                                             | `Internal Server Error`                                                                                                                                                                                                      |

**6. Notas de seguridad**

- **El cliente puede crear tareas a nombre de otro usuario** enviando `owner` (hallazgo H-API-02, pendiente). Hoy `owner` no se contrasta con la identidad del token.
- Los valores se concatenan en el `INSERT` (hallazgo H-API-03, pendiente): la validación de `status` y `priority` reduce esos dos campos, pero `title`, `description` y `owner` siguen sin parametrizar.

---

### GET /api/summary

**1. Qué hace:** devuelve un resumen de las tareas de un responsable: total, conteo por estado y cuántas de prioridad alta siguen abiertas.

**2. Autenticación:** sí. Cabecera `Authorization: Bearer <token>`.

**3. Request**

| Parámetro        | Ubicación | Tipo   | Obligatorio | Descripción                                                                     |
| ----------------- | ---------- | ------ | ----------- | -------------------------------------------------------------------------------- |
| `Authorization` | cabecera   | string | sí         | `Bearer <token>`.                                                              |
| `owner`         | query      | string | no          | Responsable a resumir. Si se omite o es `""`, se usa el `usuario` del token. |

Ejemplo:

```http
GET /api/summary HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token>
```

**4. Respuesta exitosa: 200** (`application/json`)

| Campo                | Tipo                      | Descripción                                                                                                        |
| -------------------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `owner`            | string                    | Responsable resumido (el pedido o, si no se envió, el del token).                                                  |
| `total`            | entero                    | Número de tareas del responsable.                                                                                  |
| `byStatus`         | objeto (string → entero) | Cantidad de tareas por cada estado presente. Solo aparecen los estados que tienen tareas; `{}` si no hay ninguna. |
| `highPriorityOpen` | entero                    | Tareas con prioridad `HIGH` cuyo estado no es `DONE` ni `ARCHIVED`.                                           |

```json
{"owner": "student", "total": 4, "byStatus": {"TODO": 2, "IN_PROGRESS": 2}, "highPriorityOpen": 2}
```

**5. Errores**

| Código | Cuándo                                | Cuerpo de ejemplo               |
| ------- | -------------------------------------- | ------------------------------- |
| 401     | Token ausente o inválido.             | `{"detail": "Invalid token"}` |
| 500     | `owner` contiene una comilla simple. | `Internal Server Error`       |

**6. Notas de seguridad**

- Igual que en `GET /api/tasks`: **cualquier usuario autenticado puede resumir las tareas de otro con `owner`** (H-API-02, pendiente), y `owner` se concatena en SQL (H-API-03, pendiente).

---

### POST /api/requirements

**1. Qué hace:** recibe un archivo de requerimientos y lo guarda en el servidor, a nombre del usuario autenticado.

**2. Autenticación:** sí. Cabecera `Authorization: Bearer <token>`.

**3. Request** (`Content-Type: multipart/form-data`)

| Campo    | Tipo              | Obligatorio | Descripción                                                      |
| -------- | ----------------- | ----------- | ----------------------------------------------------------------- |
| `file` | archivo (binario) | sí         | Archivo a guardar. Se guarda con el nombre que envía el cliente. |

Ejemplo:

```bash
curl -X POST http://localhost:8000/api/requirements \
  -H "Authorization: Bearer <token>" \
  -F "file=@requisitos.txt;type=text/plain"
```

**4. Respuesta exitosa: 201** (`application/json`)

| Campo        | Tipo   | Descripción                                                                                                                   |
| ------------ | ------ | ------------------------------------------------------------------------------------------------------------------------------ |
| `owner`    | string | `usuario` del token.                                                                                                         |
| `fileName` | string | Nombre del archivo tal como lo envió el cliente.                                                                              |
| `storedAt` | string | Ruta del archivo en el servidor (directorio `WORKSHOP_UPLOAD_DIR` + nombre). Depende del servidor y no debe usarse como URL. |
| `size`     | entero | Tamaño en bytes.                                                                                                              |

```json
{"owner": "student", "fileName": "requisitos.txt", "storedAt": "C:\\Users\\Usuario\\AppData\\Local\\Temp\\tmprgji0c77\\up\\requisitos.txt", "size": 27}
```

(`storedAt` es un ejemplo de una ejecución local en Windows; en otro entorno la ruta es distinta.) Si se sube otro archivo con el mismo nombre, se sobrescribe.

**5. Errores**

| Código | Cuándo                                                                                  | Cuerpo de ejemplo                                                                                      |
| ------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| 401     | Token ausente o inválido.                                                               | `{"detail": "Invalid token"}`                                                                        |
| 422     | Falta el campo `file`.                                                                 | `{"detail": [{"type": "missing", "loc": ["body", "file"], "msg": "Field required", "input": null}]}` |
| 500     | El nombre de archivo incluye un subdirectorio que no existe (por ejemplo `sub/x.txt`). | `Internal Server Error`                                                                              |

**6. Notas de seguridad**

- **El nombre del archivo no se normaliza** y no hay límite de extensión ni de tamaño; el archivo se lee completo en memoria (hallazgo H-API-04, pendiente). No suba nombres con rutas y no asuma que el servidor valida el tipo de archivo.
- `storedAt` expone la ruta absoluta del servidor (parte del contrato actual; se resuelve con H-API-04).
- Un archivo del mismo nombre se sobrescribe sin aviso, también entre usuarios distintos.

---

### GET /api/backend-health

**1. Qué hace:** consulta el estado del servicio de autenticación desde la API y devuelve su código HTTP y su respuesta.

**2. Autenticación:** sí. Cabecera `Authorization: Bearer <token>`.

**3. Request**

| Parámetro        | Ubicación | Tipo   | Obligatorio | Descripción        |
| ----------------- | ---------- | ------ | ----------- | ------------------- |
| `Authorization` | cabecera   | string | sí         | `Bearer <token>`. |

No recibe parámetros de query ni cuerpo. La API consulta con `GET` la URL de `AUTH_HEALTH_URL` (por defecto `http://localhost:8080/q/health`) con un tiempo máximo de 3 segundos.

```http
GET /api/backend-health HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token>
```

**4. Respuesta exitosa: 200** (`application/json`). Se devuelve 200 aunque el servicio de autenticación responda con error o no esté disponible; el estado real está en `status`.

| Campo           | Tipo   | Descripción                                                                                                                                                         |
| --------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `requestedBy` | string | `usuario` del token.                                                                                                                                               |
| `status`      | entero | Código HTTP de la respuesta del servicio de autenticación, o `0` si no se pudo obtener respuesta (conexión rechazada, tiempo agotado o cuerpo que no es UTF-8). |
| `body`        | string | Cuerpo de la respuesta del servicio de autenticación, tal cual (texto); si `status` es `0`, el texto fijo `Auth service unavailable`.                         |

Servicio disponible (ejecución local con un servidor de pruebas que responde `{"status":"UP","checks":[]}`):

```json
{"requestedBy": "student", "status": 200, "body": "{\"status\":\"UP\",\"checks\":[]}"}
```

Servicio no disponible:

```json
{"requestedBy": "student", "status": 0, "body": "Auth service unavailable"}
```

**5. Errores**

| Código | Cuándo                    | Cuerpo de ejemplo               |
| ------- | -------------------------- | ------------------------------- |
| 401     | Token ausente o inválido. | `{"detail": "Invalid token"}` |

No hay otros códigos de error documentados para este endpoint: los fallos de conexión con el servicio de autenticación se devuelven como 200 con `status: 0`.

**6. Notas de seguridad**

- El detalle técnico del fallo (host, puerto, excepción) no se envía al cliente; solo se registra en el log del servidor.
- `body` reenvía el contenido de la respuesta del servicio de autenticación sin filtrar; solo debe usarse para diagnóstico.
- La URL consultada la define el servidor (`AUTH_HEALTH_URL`); el cliente no puede cambiarla.

---

### Cambios respecto al comportamiento original

Cambios aprobados por el usuario en `PLAN.md` (registrados con su cita) y verificados por pruebas en `api/tests/`:

| ID       | Cambio visible para un consumidor                                                                                                                                                                                  |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| H-API-08 | CORS limitado a los orígenes de `WORKSHOP_CORS_ORIGINS` (antes cualquier origen), métodos `GET`/`POST`.                                                                                                    |
| H-API-09 | El 401 antes devolvía `"Invalid token: <detalle>"`; ahora `"Invalid token"`. Con el servicio de autenticación caído, `body` antes traía el texto de la excepción; ahora `"Auth service unavailable"`. |
| H-API-10 | `POST /api/tasks` antes aceptaba cualquier valor (título vacío, estados o prioridades arbitrarios, números convertidos a texto); ahora responde 422 en esos casos.                                            |

Sin cambios: rutas, métodos, códigos 200/201/401, nombres de los campos de las respuestas.

### Riesgos de seguridad pendientes

| ID       | Riesgo                                                                                                                | Estado    |
| -------- | --------------------------------------------------------------------------------------------------------------------- | --------- |
| H-API-01 | Token Base64 con secreto compartido, sin firma, emisor ni audiencia: un token puede fabricarse conociendo el secreto. | Pendiente |
| H-API-02 | `owner` enviado por el cliente prevalece sobre la identidad del token (consulta, resumen y creación).              | Pendiente |
| H-API-03 | SQL concatenado con `owner`, `title`, `description`, `status` y `priority`.                                 | Pendiente |
| H-API-04 | Subida de archivos sin normalizar nombre, sin límite de extensión ni de tamaño.                                    | Pendiente |
| H-API-12 | Dependencia transitiva `starlette 0.50.0` con avisos conocidos.                                                     | Pendiente |

Cuando se resuelvan H-API-01 a H-API-04, este documento debe actualizarse: cambiarán el significado de `owner` (H-API-02), los errores 401/422/500 y las reglas de `POST /api/requirements`.

### Preguntas abiertas

1. ¿El servicio de autenticación emite exactamente el formato `usuario|rol|expiracion|secreto` y con el mismo secreto? Este documento no lo verificó (no se lee código de `auth/`).
2. ¿Qué contenido tiene la respuesta real de salud del servicio de autenticación? El ejemplo usa un servidor local de pruebas.
3. ¿Qué espera `web` ante el cambio del 401, los 422 de `POST /api/tasks` y la restricción de CORS? No se verificó contra `web`.
4. ¿Cuál será el comportamiento definitivo de `owner` (¿se ignorará, se restringirá por rol?) cuando se resuelva H-API-02? El `rol` del token hoy no se usa.
5. ¿Cuál será la lista de extensiones y el tamaño máximo permitidos en `POST /api/requirements`? Hoy no existen.
6. El origen por defecto de CORS (`http://localhost:4200`) sale de `README.md`; falta confirmar el origen real del frontend en otros entornos.
7. Los valores de `status` y `priority` de tareas ya existentes en una BD antigua no se validan al leer; podrían aparecer valores fuera de los listados.
