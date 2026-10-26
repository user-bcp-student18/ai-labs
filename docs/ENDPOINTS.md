# Contrato HTTP observado por web

Este documento describe los dos endpoints externos que consume actualmente el frontend web. Los contratos siguientes son **observados en el código y en pruebas locales con dobles**; no hay una especificación de servidor ni un contrato backend acordado disponible. Los ejemplos de respuesta son formas de datos usadas por los tipos y pruebas del frontend, no capturas de respuestas de un servidor ejecutándose.

## POST /auth/login

### 1. Quién lo llama

La ruta `/login` muestra `LoginComponent` (`web/src/app/app.routes.ts:5-6`). Tras validar que username y password no estén vacíos, el componente llama a `AuthService.login()` (`web/src/app/login/login.component.ts:31-45`; `web/src/app/core/auth.service.ts:7-16`).

URL configurada: `http://localhost:8080/auth/login` (`web/src/environments/environment.ts:1`).

### 2. Qué envía

El cliente no establece encabezados HTTP adicionales en la llamada. Axios serializa el objeto de login como cuerpo JSON; el timeout configurado es de 5000 ms (`web/src/app/core/auth.service.ts:8-15`).

| Ubicación | Campo | Tipo observado | Origen |
|---|---|---|---|
| Body JSON | `username` | string | Valor del campo de usuario; se envía el valor original después de validar que `trim()` no esté vacío (`web/src/app/login/login.component.ts:33-46`). |
| Body JSON | `password` | string | Valor del campo de contraseña; se envía el valor original después de validar que `trim()` no esté vacío (`web/src/app/login/login.component.ts:37-46`). |
| Body JSON | `client` | string | Constante `angular-workshop` (`web/src/environments/environment.ts:4`; `web/src/app/core/auth.service.ts:8-12`). |

Ejemplo construido con las credenciales ficticias del laboratorio documentadas en `README.md`:

```http
POST /auth/login HTTP/1.1
Host: localhost:8080
Content-Type: application/json

{
  "username": "student",
  "password": "Workshop123!",
  "client": "angular-workshop"
}
```

### 3. Qué espera recibir en éxito

Axios trata como respuesta exitosa por defecto un estado HTTP 2xx; el frontend no fija ni comprueba un código exacto. El tipo de respuesta declara `token` y `user` como opcionales (`web/src/app/core/auth.models.ts:11-14`). El componente solo comprueba que `token` sea truthy; guarda el token y `user` —o `{}` si falta— y navega a `/dashboard` (`web/src/app/login/login.component.ts:47-54`; `web/src/app/core/session.service.ts:65-69`).

| Campo leído por el frontend | Tipo declarado | Uso |
|---|---|---|
| `token` | string opcional | Su presencia habilita el guardado de sesión y la navegación. |
| `user` | `AuthUser` opcional | Se guarda en sesión; el modelo permite `username` y `displayName` opcionales (`web/src/app/core/auth.models.ts:6-9`). |

Status HTTP aceptado por Axios: cualquier 2xx; el código concreto no está indicado en el frontend. Ejemplo JSON compatible con la prueba unitaria (no es una respuesta capturada del servidor):

```json
{
  "token": "test-token",
  "user": {
    "username": "student"
  }
}
```

El código no documenta el código HTTP concreto de éxito, la obligatoriedad de `user` ni otros campos de respuesta. Son preguntas abiertas para quien mantenga el backend.

### 4. Cómo reacciona la UI ante errores o respuestas inesperadas

| Caso | Reacción observada |
|---|---|
| Username vacío o solo espacios | No envía la solicitud; muestra `Ingrese un usuario.` (`web/src/app/login/login.component.ts:33-35`). |
| Password vacío o solo espacios | No envía la solicitud; muestra `Ingrese una contraseña.` (`web/src/app/login/login.component.ts:37-39`). |
| HTTP no exitoso, incluido un posible 401 por credenciales inválidas | Axios rechaza la llamada. El `catch` muestra `No se pudo autenticar a {username}.`; no muestra el detalle del backend (`web/src/app/login/login.component.ts:55-57`). El backend no está especificado aquí, así que el código de estado para credenciales inválidas es una pregunta abierta. |
| Timeout | La llamada tiene timeout de 5000 ms. Si Axios rechaza por timeout, el mismo `catch` muestra el mensaje genérico de autenticación; no hay reintento (`web/src/app/core/auth.service.ts:13-15`; `web/src/app/login/login.component.ts:55-57`). |
| Error de red u otra excepción de Axios | Muestra el mismo mensaje genérico; `busy` vuelve a `false` en `finally` (`web/src/app/login/login.component.ts:55-59`). |
| Respuesta 2xx sin token, con token vacío o sin token utilizable | Muestra `El backend respondió sin token.`; no guarda sesión ni navega (`web/src/app/login/login.component.ts:47-49`). |
| Respuesta 2xx con token, sin `user` | Guarda `{}` como usuario junto al token y preferencias; navega al dashboard (`web/src/app/login/login.component.ts:51-54`). |
| Cuerpo malformado o respuesta inesperada que provoque una excepción al leerla | La excepción cae en el `catch` y se muestra el mensaje genérico. No hay validación de esquema en runtime. |

### 5. Notas de seguridad

- Username y password se envían en el body JSON a la URL configurada; no se observó un canal TLS en la URL local actual (`web/src/environments/environment.ts:1`).
- El token y el usuario se almacenan mediante `SessionService` en `localStorage`; el servicio centraliza lectura, escritura y borrado, pero esto no hace que el token sea inaccesible a JavaScript (`web/src/app/core/session.service.ts:12-19,65-73`).
- El mensaje de error se renderiza como texto interpolado, no con `[innerHTML]` (`web/src/app/login/login.component.html:39`).
- El componente no expone en la UI el detalle del error de login que recibe Axios (`web/src/app/login/login.component.ts:55-57`).
- No se afirma aquí cómo el servidor valida credenciales, protege el transporte fuera del entorno local, emite tokens o responde a credenciales inválidas.

## GET /api/tasks

### 1. Quién lo llama

La ruta `/dashboard` carga `DashboardComponent` (`web/src/app/app.routes.ts:9-10`). En la inicialización, si hay token, el componente obtiene el username de la sesión y delega la lectura a `TasksService.getTasks()` (`web/src/app/dashboard/dashboard.component.ts:45-56`; `web/src/app/core/tasks.service.ts:7-14`).

URL configurada: `http://localhost:8000/api/tasks` (`web/src/environments/environment.ts:3`).

### 2. Qué envía

La solicitud no tiene body. Axios recibe el propietario como query parameter y el token en el encabezado Authorization (`web/src/app/core/tasks.service.ts:8-13`).

| Ubicación | Campo | Tipo observado | Origen |
|---|---|---|---|
| Query parameter | `owner` | string | Username de `SessionService`; si no hay username string, el componente pasa cadena vacía (`web/src/app/dashboard/dashboard.component.ts:53-56`). |
| Header | `Authorization` | string | `Bearer ` seguido del token leído desde la sesión (`web/src/app/core/tasks.service.ts:9-12`; `web/src/app/core/session.service.ts:13-15`). |
| Body | Ninguno | — | No se pasa body a `axios.get()` (`web/src/app/core/tasks.service.ts:8-13`). |

Ejemplo con valores ficticios usados por el test del frontend:

```http
GET /api/tasks?owner=student HTTP/1.1
Host: localhost:8000
Authorization: Bearer test-token
```

### 3. Qué espera recibir en éxito

Axios considera exitosa por defecto una respuesta HTTP 2xx. El servicio declara `response.data` como `Task[]` (`web/src/app/core/tasks.service.ts:8-14`), pero no valida el esquema en runtime. No se especifica un código exacto de éxito.

| Campo de tarea | Tipo declarado | Uso observado |
|---|---|---|
| `title` | string requerido | Se muestra como título en la tarjeta. |
| `description` | string requerido | Se muestra en la tarjeta. |
| `status` | string requerido en TypeScript | Se filtra `ARCHIVED` y se convierte en etiqueta visible. Un valor nulo/ausente no está manejado de forma segura actualmente. |
| `priority` | string opcional | Se usa para la etiqueta y el orden de tareas. |
| `owner` | string opcional | Se usa para la etiqueta de tarea. |
| `label` | string opcional | Puede ser reemplazado por el label calculado en el dashboard. |

Los campos y tipos provienen de `web/src/app/core/task.models.ts:1-8`. Status HTTP aceptado por Axios: cualquier 2xx; el código concreto no está indicado en el frontend. Ejemplo sintético de JSON, basado en los valores del fixture de `web/src/app/dashboard/dashboard.component.spec.ts:60-68`, no en una respuesta capturada del backend:

```json
[
  {
    "title": "Low",
    "status": "TODO",
    "priority": "low",
    "owner": "student"
  }
]
```

El dashboard conserva el array recibido en `tasks`, excluye de `visibleTasks` los elementos cuyo status sea exactamente `ARCHIVED`, agrega un label y ordena por prioridad descendente mediante comparación lexical (`web/src/app/dashboard/dashboard.component.ts:57-60`). La respuesta real y el orden de prioridad acordado con el servidor no están documentados.

### 4. Cómo reacciona la UI ante errores o respuestas inesperadas

| Caso | Reacción observada |
|---|---|
| No hay token en sesión | No llama al endpoint; navega a `/login` (`web/src/app/dashboard/dashboard.component.ts:45-50`). |
| Token inválido o expirado, si el servidor responde con HTTP no exitoso | Axios rechaza. La UI muestra `response.data.detail` si es un string; si no, `error.message`; si no hay mensaje estructurado, muestra `No se pudo cargar el dashboard`. Apaga el indicador de carga. No borra el token ni redirige automáticamente (`web/src/app/dashboard/dashboard.component.ts:62-75,89-94`). El status que devuelve el servidor es pregunta abierta. |
| Timeout | `TasksService` no pasa una opción timeout ni configura reintentos; no se establece aquí un límite específico. Si Axios rechaza la llamada por timeout, se usa la lógica de error anterior. |
| Error de red | Muestra el mensaje de Axios si está disponible; si no, el mensaje genérico. Apaga el indicador de carga (`web/src/app/dashboard/dashboard.component.ts:62-75,89-94`). |
| Respuesta no exitosa con `detail` string | Muestra ese `detail` como texto interpolado en la plantilla del dashboard (`web/src/app/dashboard/dashboard.component.ts:89-94`; `web/src/app/dashboard/dashboard.component.html:16`). |
| Cuerpo exitoso que no sea un array | El acceso a `.filter()` falla dentro del `try`; el `catch` apaga la carga y muestra el mensaje de excepción si existe, o el genérico (`web/src/app/dashboard/dashboard.component.ts:53-75`). No hay validación explícita de la forma de `response.data`. |
| Elemento sin `status` | El filtro no lo considera `ARCHIVED`, pero al mostrar la tarjeta `statusLabel()` llama `toUpperCase()` directamente. Puede fallar el render del dashboard; es una regresión pendiente documentada como H-WEB-06 (`web/src/app/dashboard/dashboard.component.ts:40-41,57-60`; `web/src/app/dashboard/dashboard.component.html:21`; `HALLAZGOS.md`, H-WEB-06). |

### 5. Notas de seguridad

- El token se lee desde `SessionService` y se envía como Bearer; la sesión actualmente reside en `localStorage` (`web/src/app/core/session.service.ts:12-15`; `web/src/app/core/tasks.service.ts:8-12`). La ubicación no protege contra código JavaScript ejecutado en el mismo origen.
- El parámetro `owner` procede del usuario guardado en el frontend. El frontend no puede establecer autorización efectiva; la validación de identidad y propiedad de tareas por backend es una pregunta abierta y no se confirma aquí.
- La URL configurada es HTTP local, no HTTPS (`web/src/environments/environment.ts:3`). No se deduce el comportamiento de transporte en otros entornos.
- Los errores del dashboard se interpolan como texto, no mediante `[innerHTML]` (`web/src/app/dashboard/dashboard.component.html:16`).

## Estado del contrato

| Endpoint | Contrato observado | Contrato acordado | Riesgos o preguntas abiertas |
|---|---|---|---|
| `POST /auth/login` | Body `username`, `password`, `client`; timeout 5000 ms; el frontend requiere `token` para guardar sesión y navegar. | No se encontró una especificación compartida o aprobación backend en el alcance revisado. | Código HTTP exacto, esquema completo de éxito, respuesta por credenciales inválidas, transporte no local y emisión/expiración del token. |
| `GET /api/tasks` | Query `owner`, Bearer token; el frontend espera un array de tareas con campos indicados arriba. | No se encontró una especificación compartida o aprobación backend en el alcance revisado. | Código HTTP exacto, esquema real de tarea, comportamiento para token inválido, autorización de `owner`, timeout y validación de respuesta. |
