# Proposal

## Why

El Issue [#22](https://github.com/user-bcp-student18/ai-labs/issues/22), asociado al hallazgo `H-AUTH-01`, indica que una entrada manipulada en el login puede alterar la búsqueda de credenciales y permitir autenticarse sin conocer la contraseña. Corregir este comportamiento evita la autenticación no autorizada y preserva el acceso legítimo.

## What Changes

- **En alcance:** el endpoint `POST /auth/login` no autentica solicitudes cuyas credenciales intenten alterar la búsqueda; responde `401` y no entrega un token.
- **En alcance:** se verifica de forma observable el rechazo de la entrada de inyección indicada por el Issue tanto en el usuario como en la contraseña.
- **Fuera de alcance:** cambios en `api/`, `web/`, otros flujos de autenticación, el formato de tokens o endpoints distintos de `POST /auth/login`.
- **Comportamiento que se preserva:** el Issue pide conservar el login válido. La prueba existente confirma que `student` con `Workshop123!` recibe `200`, `user.username` igual a `student` y un `token` no nulo.
- **Baseline documental:** `docs/ENDPOINTS.md` documenta contratos de `api/`, pero no incluye `POST /auth/login`. Por ello, no se atribuye a ese documento un contrato de autenticación; el escenario de éxito preserva el comportamiento observable ya probado y el rechazo de credenciales manipuladas es el cambio solicitado por el Issue.
- No se modificarán las secciones de `api/` ni `web/` en documentos generales.

## Capabilities

### New Capabilities
- `auth-login`: comportamiento observable del inicio de sesión y manejo de credenciales válidas o manipuladas.

### Modified Capabilities
- Ninguna.

## Impact

El alcance funcional y de pruebas se limita a `auth/` y a `POST /auth/login`. No se cambian contratos de `api/` o `web/`, dependencias ni documentos generales.