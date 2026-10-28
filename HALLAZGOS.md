# Hallazgos

## Flujo observado de web

`/login` carga `LoginComponent`; `/dashboard` carga `DashboardComponent` (`web/src/app/app.routes.ts:5,9`). El formulario enlaza usuario y contraseña a propiedades del componente (`web/src/app/login/login.component.html:19,30`). Al enviar, login valida los campos y delega el request al `AuthService` (`web/src/app/login/login.component.ts:31-45`), que envía `POST` a la URL configurada con `username`, `password` y `client` (`web/src/app/core/auth.service.ts:8-16`; `web/src/environments/environment.ts:1-6`). Si la respuesta contiene `token`, `SessionService` guarda token, usuario y preferencias y el componente navega al dashboard (`web/src/app/login/login.component.ts:49-54`; `web/src/app/core/session.service.ts:65-69`).

El dashboard lee token y usuario mediante `SessionService`; si no encuentra token, navega a login (`web/src/app/dashboard/dashboard.component.ts:45-49`). Con token, llama a `TasksService`, que consulta la URL configurada pasando `owner` como parámetro y el encabezado `Authorization: Bearer ...` (`web/src/app/dashboard/dashboard.component.ts:53-56`; `web/src/app/core/tasks.service.ts:8-13`; `web/src/environments/environment.ts:1-6`). Filtra tareas `ARCHIVED`, calcula etiquetas y ordena por prioridad (`web/src/app/dashboard/dashboard.component.ts:57-60`). El botón de cierre invoca `logout()`, que borra token y usuario mediante `SessionService` y vuelve a login; no elimina las preferencias (`web/src/app/dashboard/dashboard.component.html:9`; `web/src/app/dashboard/dashboard.component.ts:77-80`; `web/src/app/core/session.service.ts:71-74`).

Este es el contrato observable desde el frontend. No se comprobó aquí la respuesta del servidor para credenciales inválidas, el comportamiento de autorización del endpoint de tareas ni la implementación de esos endpoints.

## Matriz de seguimiento

Ordenada de mayor a menor severidad. Los estados iniciales son `Pendiente`; una versión de dependencia listada en el reto o una práctica riesgosa no confirma por sí sola una vulnerabilidad explotable.

| id | componente | hallazgo | tipo | explicacion | evidencia (archivo:linea) | severidad | estado |
|---|---|---|---|---|---|---|---|
| H-WEB-03 | web | Dependencias directas `axios` y `lodash` con advisories reportados | Vulnerabilidad | `npm audit --audit-level=moderate` reportó vulnerabilidades altas para las versiones declaradas. No se pudieron actualizar o retirar: `npm uninstall lodash` falló con `Cannot read properties of null (reading 'children')` antes de cambiar manifiestos; el lockfile preexistente se conservó. | `web/package.json:19-20` | alta | Pendiente |
| H-WEB-01 | web | Token de sesión en `localStorage` | Vulnerabilidad | El token sigue accesible desde JavaScript en el origen. No se cambió el mecanismo de almacenamiento: falta acordar con backend una estrategia de sesión que no exponga secretos al frontend. | `web/src/app/core/session.service.ts:13-15,65-73` | media | Pendiente |
| H-WEB-02 | web | Componentes acoplados a HTTP, URLs, sesión y navegación | Refactor | Resuelto: llamadas HTTP movidas a `AuthService` y `TasksService`, URLs y cliente centralizados en `environment.ts`, y acceso a sesión centralizado en `SessionService`; se conservaron endpoints, payload de login, encabezado Bearer, navegación y ciclo observado. | `web/src/app/core/auth.service.ts:1-17`; `web/src/app/core/tasks.service.ts:1-14`; `web/src/app/core/session.service.ts:1-74`; `web/src/environments/environment.ts:1-6` | media | Resuelto |
| H-WEB-06 | web | Tipado del estado de tarea pierde tolerancia a status nulo | Bug | El modelo declara `status` obligatorio, pero la respuesta HTTP no se valida en runtime. `statusLabel` ahora llama directamente a `toUpperCase()`; un `status` nulo o ausente hace fallar el dashboard. El código previo protegía ese caso con `(status || '')`, y las pruebas actuales solo usan estados string. | `web/src/app/core/task.models.ts:1-8`; `web/src/app/dashboard/dashboard.component.ts:40-41`; `web/src/app/dashboard/dashboard.component.spec.ts:60-80,125-128` | media | Pendiente |
| H-WEB-04 | web | Mensaje dinámico mostrado mediante `[innerHTML]` | Sugerencia | Resuelto: el mensaje de login ahora se muestra con interpolación de texto; el error de autenticación usa texto genérico y no concatena detalles del backend en HTML. | `web/src/app/login/login.component.ts:31-54`; `web/src/app/login/login.component.html:39` | baja | Resuelto |
| H-WEB-05 | web | Cobertura de pruebas de flujos de login, sesión y dashboard | Sugerencia | Resuelto: se cubren caminos felices, login seguido de carga de tareas con sesión compartida, campos vacíos, respuesta sin token, servicio de autenticación no disponible, timeout e invalidación de token simulada. En la ejecución actual pasaron 28 tests; la cobertura global es 254/282 líneas (90.07%) y los archivos de producción de los flujos de login, dashboard y sesión cubiertos están al 100%. No se hicieron llamadas a backends reales. | `web/src/app/login/login.component.spec.ts:50-137`; `web/src/app/dashboard/dashboard.component.spec.ts:51-181`; `web/src/app/core/session.service.spec.ts:1-112` | baja | Resuelto |
| H-WEB-07 | web | Tipado y responsabilidades de componentes | Refactor | Pendiente: se eliminaron los `any` de los componentes y utilidad afectados, se añadieron modelos tipados y retornos tempranos; no se confirmó duplicación. Sin embargo, el cambio también introdujo el caso no manejado de `status` nulo en H-WEB-06, por lo que el hallazgo no se considera completamente resuelto hasta restaurar y probar ese comportamiento defensivo. | `web/src/app/login/login.component.ts:14-57`; `web/src/app/dashboard/dashboard.component.ts:22-86`; `web/src/app/core/auth.models.ts:1-22`; `web/src/app/core/task.models.ts:1-8`; `web/src/app/utils/legacy-format.ts:1-9`; `web/src/app/dashboard/dashboard.component.ts:40-41` | media | Pendiente |

## Evidencia pendiente

- `docs/ENDPOINTS.md` no existe; el contrato registrado arriba se deriva únicamente del código de `web/`.
- `HALLAZGOS.md` no existía antes de este paso, así que no había filas de otros componentes ni historial previo que conservar.
- No se revisó el backend dentro de este alcance. El frontend demuestra que envía los valores de login, pero no permite determinar si llegan concatenados a SQL o enlazados como parámetros.
- Se ejecutaron `npm test -- --reporter=verbose`, `npm run test:coverage` y `npm run build` desde `web/`; los resultados y las limitaciones están en la sección web de `PLAN.md`.
- `npm audit --audit-level=moderate` se ejecutó desde `web/` y reportó 25 vulnerabilidades en el árbol (10 moderadas, 9 altas, 6 críticas). `axios` y `lodash` se reportaron con advisories altos. La actualización quedó pendiente porque `npm uninstall lodash` falló; el lockfile preexistente no se modificó en ese intento.
- `H-WEB-01` permanece pendiente: no se acordó una nueva estrategia de sesión con backend y no se movieron secretos al frontend.

## Candidatos de discovery — web (2026-10-27)

### H-WEB-01 — Token de sesión accesible desde JavaScript
- Estado: CANDIDATO
- Evidencia: `web/src/app/core/session.service.ts:13-15,65-73`.
- Impacto: el token guardado en `localStorage` es accesible desde JavaScript ejecutado en el origen; no se confirmó explotación.
- Prioridad propuesta: media.
- Contrato potencialmente afectado: manejo de sesión entre frontend y backend; la estrategia alternativa no está acordada.
- Cómo validarlo: acordar la estrategia con backend y comprobar con una prueba automatizada que el token no sea legible desde JavaScript, manteniendo las pruebas de inicio y cierre de sesión.

### H-WEB-03 — Dependencias directas con advisories reportados
- Estado: CANDIDATO
- Evidencia: `web/package.json:19-20`; comando `cd web; npm audit --audit-level=moderate` reportó advisories de severidad alta para `axios@0.31.0` y `lodash@4.17.21` y, en total, 25 vulnerabilidades en el árbol (10 moderadas, 9 altas y 6 críticas).
- Impacto: las dependencias instaladas incluyen versiones que el audit marca como afectadas; la exposición concreta depende de uso y alcanzabilidad, no comprobados en este análisis.
- Prioridad propuesta: alta.
- Contrato potencialmente afectado: comportamiento de solicitudes HTTP realizadas mediante Axios; no se identificó un contrato funcional específico afectado.
- Cómo validarlo: revisar el resultado vigente del audit y verificar después de cualquier actualización que el audit ya no reporte advisories para esas dependencias, sin degradar las pruebas existentes.

### H-WEB-06 — Estado de tarea nulo o ausente no tolerado
- Estado: CANDIDATO
- Evidencia: `web/src/app/core/task.models.ts:1-8` tipa `status` como obligatorio; `web/src/app/dashboard/dashboard.component.ts:40-41` llama `toUpperCase()` sin validar el valor; `web/src/app/dashboard/dashboard.component.html:25` invoca el método al renderizar; los casos del test en `web/src/app/dashboard/dashboard.component.spec.ts:60-80,187-192` usan valores string.
- Impacto: una tarea con `status` nulo o ausente puede interrumpir el renderizado del dashboard.
- Prioridad propuesta: media.
- Contrato potencialmente afectado: forma de la respuesta de `/api/tasks` y renderizado de estados de tarea.
- Cómo validarlo: agregar pruebas de respuesta con `status` nulo y ausente, y verificar que el dashboard no falle y que el comportamiento esperado quede definido.

### H-WEB-08 — La sesión queda almacenada ante respuesta 401
- Estado: CANDIDATO
- Evidencia: `web/src/app/dashboard/dashboard.component.ts:45-49,65-72` carga tareas con el token y, ante error, solo muestra un mensaje; `web/src/app/dashboard/dashboard.component.spec.ts:137-152` verifica que ante 401 se conserva el token y no se navega a login.
- Impacto: ante un token rechazado, el cliente mantiene la sesión local y el usuario permanece en el dashboard con un error; la política esperada de sesión inválida no está documentada aquí.
- Prioridad propuesta: media, pendiente de confirmar el contrato con backend.
- Contrato potencialmente afectado: comportamiento de expiración o rechazo de sesión del endpoint `/api/tasks`.
- Cómo validarlo: acordar con backend el comportamiento esperado para 401 y ejecutar una prueba funcional que confirme limpieza de sesión y navegación, o documente explícitamente el comportamiento acordado.
