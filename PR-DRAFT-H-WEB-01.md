> PR listo para revisión humana. Fusionable en Git (`MERGEABLE`), pero los checks remotos fallan: `dependencies` (Dependency graph desactivado en el repositorio) y `web` (`npm ci` falla con `Cannot read properties of null (reading 'edgesOut')`; `main` también tiene `AI Labs CI` en fallo). H-WEB-01 está **diferido**; este PR no implementa su cambio. No fusionar sin aprobación humana.

## Cambio

- Issue: no hay issue de GitHub; el hallazgo es H-WEB-01 en `HALLAZGOS.md`.
- IDs H-xx: H-WEB-01 (diferido por condición humana). Las filas H-WEB-02 a H-WEB-06 quedan fuera de este borrador.
- Componente afectado: `web/`.
- Comportamiento anterior: el token de sesión se guarda en `localStorage` (`web/src/app/core/session.service.ts:13-15,65-73`).
- Resultado de este PR: **sin cambio de código para H-WEB-01**. Se implementó en `cda9621` (estrategia B, token solo en memoria) y se revirtió en `e272434` porque `PLAN.md` registra la aprobación de H-WEB-01 como "aprobado con condición": no cambiar el almacenamiento del token sin una estrategia de sesión acordada con backend. Ese acuerdo no existe en el repositorio.
- Resultado esperado: H-WEB-01 sigue pendiente; `web/` queda igual a `9e2fe6a`.

## Comprobación

Comandos ejecutados tras la reversión (cwd raíz, `python tools/lab.py test web`):

| Comando | Resultado real |
|---|---|
| `npm test` (vía `lab.py test web`) | 4 archivos, 28 pruebas: pasaron 28, fallaron 0 |
| `npm run test:coverage` | Cobertura global 90.07% de líneas; `session.service.ts`, `auth.service.ts`, `tasks.service.ts`, login y dashboard al 100% |
| `npm run build` | Build correcto; persiste advertencia de CommonJS de `axios` (ya existente) |

Referencias que sustentan el cambio: `PLAN.md` (sección "Registro de aprobación", fila H-WEB-01), `docs/ENDPOINTS.md` y `docs/TESTING.md` (describen el token en `localStorage`, que coincide con el estado restaurado).

Pendientes y no ejecutados:
- No se validó el flujo contra backends reales.
- `npm audit` (H-WEB-03) no se volvió a ejecutar en esta sesión; el resultado registrado en `PLAN.md` es de revisiones anteriores.
- H-WEB-06 sigue con regresión abierta (`statusLabel` con status nulo/ausente) según `PLAN.md`.
- Hallazgo candidato fuera de alcance: `api/app/main.py` valida el Bearer decodificando base64 y comparando con una constante en código, sin firma. No se registró en `HALLAZGOS.md` porque no ha sido aprobado.

## Revisión humana

- Decisión pendiente de la persona revisora: confirmar que H-WEB-01 se mantiene diferido.
- Si se decide implementar H-WEB-01, se requiere primero una estrategia de sesión acordada con backend (registrada en `PLAN.md`) y una nueva aprobación. La salida de este agente no sustituye esa revisión.
- Pendiente: `HALLAZGOS.md` (discovery y renombrado de H-WEB-06 a H-WEB-07), `HU-01.md`, `.agents/` y `skills-lock.json` siguen sin confirmar en Git.
- Rama: `day2/skill-mcp`. AGENTS.md indica `day1/prompting`; esta rama no se ha cambiado.
- Revertir este borrador: no aplica (no hay cambio de código); para deshacer el intento, `git revert e272434` restaura la implementación de H-WEB-01 si se aprueba más adelante.
