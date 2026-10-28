# Revision local de autorizacion

- PR: https://github.com/user-bcp-student18/ai-labs/pull/22
- Repositorio y numero: user-bcp-student18/ai-labs, #22
- Base: main @ 2e199ecaddfdd72e5d17bfb8ca71f3657e48248f
- Cabeza: day2/skill-mcp @ a9c2850d39c9b74ca3910e0f1538f75c49ec2123
- Criterio: autorizacion de acceso y modificacion de recursos.
- Cobertura y limitaciones: diff completo obtenido por MCP (13 de 13 archivos, 657 lineas de diff; la lista de archivos cabe en una sola pagina de 100). Base y cabeza verificadas como estables en una segunda consulta. Revisados: skills (`.agents/skills/*`, `.github/skills/feature-intake-spec-checklist/*`), `.vscode/mcp.json`, `HALLAZGOS.md`, `HU-01.md`, `PR-DRAFT-H-WEB-01.md`, `skills-lock.json`. Contexto de codigo leido en el SHA de cabeza: `web/src/app/dashboard/dashboard.component.ts` y `web/src/app/core/session.service.ts`. No disponible en esta revision: codigo de backend (API y auth) para confirmar la validacion de token del lado servidor, y el spec `web/src/app/dashboard/dashboard.component.spec.ts`, que el diff referencia pero no se leyo. El servidor MCP `github-official-readonly` devolvio error de cabeceras (`header mismatch`); la consulta se realizo con `github-mcp-server`.

## Observaciones

### Sesion local conservada tras error al cargar tareas (posible 401) — riesgo por confirmar
- Evidencia del diff: `HALLAZGOS.md`, lado cabeza, linea 542 del diff guardado (`pr22.diff`), `- Impacto: ante un token rechazado, el cliente mantiene la sesion local y el usuario permanece en el dashboard con un error; la politica esperada de sesion invalida no esta documentada aqui.`; referencia el contexto de `web/src/app/dashboard/dashboard.component.ts`, lineas 45-49 y 68-73 en cabeza. Enlace directo al diff: no proporcionado por MCP; URL del PR y SHA indicados arriba.
- Analisis: en el SHA de cabeza, `ngOnInit` lee el token de `SessionService` (lineas 45-49) y lo envia a `TasksService.getTasks` (lineas 53-56). Si la llamada falla, el bloque `catch` (lineas 68-73) solo asigna `this.error` y pone `loading = false`; no limpia la sesion ni redirige a login. Actor: usuario con token local rechazado por el servidor. Recurso: lista de tareas. El cliente no concede acceso por si mismo: la decision de autorizacion sobre las tareas corresponde al backend, que este PR no modifica, por lo que no se demuestra acceso no autorizado. La politica de invalidacion de sesion tras un 401 no esta definida en el repositorio.
- Confirmacion: prueba automatizada del dashboard con `getTasks` que responde 401: resultado esperado si la politica es invalidar la sesion, que `clearSession` se llame y se navegue a `/login`; resultado actual esperado, segun el spec referenciado en el diff, que el token se conserve y no haya navegacion. Confirmar tambien con backend que el token rechazado no concede acceso a recursos.
- Estado de la prueba: pendiente. No se ejecuto ninguna prueba en esta revision.

## Comprobaciones realizadas

- Busqueda en el diff de terminos de autorizacion (permiso, propietario, tenant, rol, acceso, eliminar, bypass, admin, token): hallazgos solo en documentacion y en la descripcion de H-WEB-01.
- Eliminaciones: unica linea eliminada del diff en `HALLAZGOS.md` (fila H-WEB-06 duplicada por H-WEB-07). No elimina ningun control de acceso.
- Cambios de codigo de sesion: `web/src/app/core/session.service.ts` no esta en el PR; en cabeza conserva `getToken`, `saveSession` y `clearSession` sobre `localStorage`, igual que la base segun la descripcion de H-WEB-01 (revert de `cda9621` por `e272434`). El revert no retira ningun control de autorizacion.
- `.vscode/mcp.json`: configura el servidor `github-official-readonly` con `X-MCP-Readonly: true`; el servidor `github-official` no tiene esa cabecera. Es configuracion de herramientas de desarrollo, no control de acceso a recursos de la aplicacion; no se reporta como observacion.
- Skills y documentos (`.agents/skills/*`, `.github/skills/feature-intake-spec-checklist/*`, `HU-01.md`, `PR-DRAFT-H-WEB-01.md`, `skills-lock.json`): sin logica de acceso a recursos.
- Fuera del criterio y no revisado: exposicion del token en `localStorage` (H-WEB-01, confidencialidad), pruebas generales, estado de CI del PR y compatibilidad.
- Pruebas: ninguna ejecutada en esta revision. Pendiente: `python tools/lab.py test web` (cubre la prueba de la observacion).

Revision local limitada al criterio indicado; no constituye una aprobacion del PR.
