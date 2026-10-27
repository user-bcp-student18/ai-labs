# Evidencia H-WEB-01 — token de sesión en memoria (estrategia B)

Componente: `web`
Hallazgo: H-WEB-01 (`web/src/app/core/session.service.ts:13-15,65-73`)
Modo: solo local (Día 1 / sin push, sin PR, sin remotos nuevos)
Rama: `day2/skill-mcp`

## Cambio

- `SessionService` guarda el token solo en memoria (`private token`), no en `localStorage`.
- El constructor elimina la clave heredada `workshop_token` de `localStorage`.
- `saveSession` no escribe el token; `clearSession` lo anula en memoria y borra la clave de usuario. Las preferencias se conservan.
- Specs actualizados: `session.service.spec.ts` (2 pruebas nuevas), `login.component.spec.ts` (aserción de token ausente), `dashboard.component.spec.ts` (sesión compartida en memoria).

## Comandos y resultados

| Comando | Resultado |
|---|---|
| `python tools/lab.py test web` (línea base antes del cambio) | 28/28 pruebas OK, cobertura 90%, build OK |
| `python tools/lab.py test web` (tras el cambio, primera ejecución) | Fallo de transformación en `dashboard.component.spec.ts:106` (edición con error de sintaxis; corregido) |
| `python tools/lab.py test web` (tras corrección) | 30/30 pruebas OK, build OK (solo advertencia de `axios` no ESM, ya existente) |
| Cobertura por archivo (tras corrección) | `session.service.ts`, `auth.service.ts`, `tasks.service.ts`, `login.component.ts` y `dashboard.component.ts` con líneas al 100%; total 90.2% |

Criterio de meta ≥85% del código modificado: cumplido.

## Riesgo residual (no resuelto por B)

- Un token en memoria sigue siendo legible desde cualquier JavaScript de la misma página (XSS). B elimina la persistencia en `localStorage`, no la exposición en el contexto JS. No se debe declarar H-WEB-01 como resuelto en totalidad.
- Un recargo de página borra el token; el dashboard redirige a `/login` (comportamiento esperado de B).

## Hallazgo candidato separado (sin cambios, pendiente de revisión humana)

- Candidato: validación Bearer en `api/app/main.py` (`legacy_identity`): decodifica base64 del token y compara con una constante en código, sin firma. Afecta a la API, fuera del alcance de H-WEB-01. No se registra como H-API-NN sin aprobación. Valor del secreto omitido intencionalmente.

## Rollback

- Revertir el commit local de los cuatro archivos de `web/` listados arriba (`git revert <hash>` o `git reset --soft HEAD~1` si no se ha compartido).
