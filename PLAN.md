# Plan

## web — cambios aprobados y ejecución

**Estado:** Aprobación humana registrada para H-WEB-01 a H-WEB-06; implementación y validación completadas parcialmente según las dependencias documentadas abajo.
**IDs seleccionados y aprobados:** H-WEB-01 (condicionado), H-WEB-02, H-WEB-03, H-WEB-04, H-WEB-05 y H-WEB-06. H-WEB-01 no se implementó porque no existe una estrategia de sesión acordada con backend. H-WEB-03 no se pudo remediar porque npm falló y no se modificó el lockfile.
**Alcance:** Solo `web/` para código, configuración y pruebas. La evidencia de este componente se registra en esta sección y en las filas `H-WEB-*` de `HALLAZGOS.md`. No se modifica el contrato de `/auth/login` ni `/api/tasks`, ni se trasladan secretos al frontend.

### Comportamiento observado que debe preservarse

- `/login` valida los campos y delega el envío a `AuthService`; el servicio hace `POST` con `username`, `password` y `client` a la URL de `environment.ts`. Al recibir un token, `SessionService` almacena token, usuario y preferencias y el componente navega a `/dashboard` (`web/src/app/login/login.component.ts:31-54`; `web/src/app/core/auth.service.ts:8-16`; `web/src/app/core/session.service.ts:65-69`; `web/src/environments/environment.ts:1-6`).
- `/dashboard` redirige a `/login` si no encuentra token; con token `TasksService` consulta la URL configurada, pasando `owner` como parámetro y agregando el encabezado Bearer (`web/src/app/dashboard/dashboard.component.ts:45-56`; `web/src/app/core/tasks.service.ts:8-13`; `web/src/environments/environment.ts:1-6`).
- El dashboard filtra tareas archivadas, presenta tareas y muestra carga/error (`web/src/app/dashboard/dashboard.component.ts:57-75`).
- Logout elimina token y usuario mediante `SessionService` y navega a `/login` (`web/src/app/dashboard/dashboard.component.ts:77-80`; `web/src/app/core/session.service.ts:71-74`).
- `docs/ENDPOINTS.md` no existe. Este comportamiento observado, no un contrato backend acordado, es la base provisional de caracterización. La respuesta del backend para credenciales inválidas y la semántica de autorización de tareas no se verificaron.

### Hallazgos aprobados y alcance ejecutado

| ID       | Propuesta acotada                                                                                                                                                                                                                                | Caracterización previa y verificación posterior                                                                                                                                                                                                                           | Dependencias / riesgos                                                                                                                                                                                                                                 | Aprobación humana         |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------- |
| H-WEB-01 | Mantener diferido hasta que exista un mecanismo de sesión acordado con el backend. No reemplazar `localStorage` por otra ubicación accesible al frontend ni inventar cookies/contratos que el backend no soporte.                            | Caracterización y verificación quedan pendientes hasta acordar una estrategia de sesión que no exponga secretos al frontend. | Requiere coordinación y decisión del responsable externo de autenticación; no implementable de forma segura solo desde la evidencia disponible en `web/`. | Aprobado con condición; diferido |
| H-WEB-02 | Separar HTTP, URLs y gestión de sesión de los componentes en servicios de frontend, preservando rutas, payloads y navegación observados. Centralizar configuración de URL y acceso a sesión según las convenciones existentes en `web/`. | Caracterización previa y regresión posterior ejecutadas; detalles en el registro de ejecuciones. | Implementado junto con H-WEB-06. Se conservaron endpoints, payloads y almacenamiento observado; no introducir estrategia de sesión nueva. | Aprobado; implementado |
| H-WEB-03 | Evaluar `axios` y `lodash` con el comando de auditoría existente; cambiar o retirar dependencias solo si la salida y compatibilidad justifican el cambio.                                                                                   | Auditoría ejecutada; remediación y verificación posterior pendientes por fallo del gestor de paquetes. | El `web/package-lock.json` preexistente se preservó; no ejecutar `npm audit fix --force` ni modificar versiones fuera de evidencia/compatibilidad. | Aprobado; bloqueado |
| H-WEB-04 | Sustituir el renderizado de mensajes dinámicos mediante `[innerHTML]` por presentación de texto, preservando el contenido comprensible del estado de validación y error.                                                                    | Caracterización previa y prueba posterior de error completadas; la plantilla compiló en build. | Mensaje de error de login genérico, sin detalles internos del backend ni HTML dinámico. | Aprobado; implementado |
| H-WEB-05 | Ampliar cobertura con pruebas de flujos y reglas de negocio del login, sesión, dashboard y logout, no solo de `formatTaskLabel`.                                                                                                              | Baseline y regresión ejecutados; cobertura final registrada abajo. | Se midieron líneas por archivo y cobertura global, sin inferir cobertura del diff a partir del porcentaje global solamente. | Aprobado; implementado |
| H-WEB-06 | Reemplazar `any`, reducir anidamiento y nombres temporales poco expresivos, y extraer duplicación solo cuando el análisis confirme duplicación real. Añadir tipos de request/response para los endpoints consumidos.                       | Caracterización previa, pruebas y build pasaron, pero la revisión contra `main` detectó una regresión no caracterizada: `statusLabel` falla con un status ausente/nulo. | No se encontró evidencia suficiente de duplicación. Añadir caso de status ausente/nulo y corregir el guard antes de cerrar. | Aprobado; pendiente de corrección |

### Secuencia y ejecución

1. La persona solicitante aprobó los seis IDs; la decisión por ID, fecha y condiciones está registrada abajo.
2. Se inspeccionó el diff preexistente de `web/package-lock.json`. Se preservó sin cambios; `npm uninstall lodash` falló antes de modificarlo.
3. Se añadieron y ejecutaron pruebas de caracterización del flujo actual antes de la refactorización. Las pruebas iniciales documentaron request de login, persistencia, navegación, tareas y logout.
4. Se implementaron únicamente los alcances aprobados en `web/`. H-WEB-01 queda pendiente porque falta acordar con backend una estrategia de sesión; H-WEB-03 sigue pendiente por el fallo del gestor de paquetes.
5. Se ejecutaron pruebas de regresión, cobertura y build. Los comandos y resultados reales están en el registro siguiente.
6. Se actualizaron solo las filas `H-WEB-*` de `HALLAZGOS.md`; los IDs pendientes siguen visibles y no se marcan resueltos.

### Registro de aprobación

| ID       | Decisión humana (aprobar / rechazar / diferir) | Persona o rol | Fecha | Alcance o condiciones |
| -------- | ----------------------------------------------- | ------------- | ----- | --------------------- |
| H-WEB-01 | Aprobado con condición | Carla Llano (solicitante) | 2026/10/26 | No cambiar almacenamiento del token sin estrategia de sesión acordada con backend; no trasladar secretos al frontend. |
| H-WEB-02 | Aprobado | Carla Llano (solicitante) | 2026/10/26 | Preservar endpoints, payloads y comportamiento observado. |
| H-WEB-03 | Aprobado | Carla Llano (solicitante) | 2026/10/26 | Auditar dependencias; preservar el diff previo del lockfile. |
| H-WEB-04 | Aprobado | Carla Llano (solicitante) | 2026/10/26 | Mantener mensajes visibles sin HTML dinámico. |
| H-WEB-05 | Aprobado | Carla Llano (solicitante) | 2026/10/26 | Añadir pruebas de flujo y medir cobertura del código modificado. |
| H-WEB-06 | Aprobado | Carla Llano (solicitante) | 2026/10/26 | Tipar y simplificar; extraer duplicación solo si se confirma. |

### Registro de ejecuciones

| Componente | IDs | Comando y cwd | Resultado real |
|---|---|---|---|
| web | H-WEB-05, H-WEB-02, H-WEB-04, H-WEB-06 | `npm test -- --reporter=verbose` (cwd `web/`), caracterización previa | Primer intento falló porque Vitest no cargaba `@angular/compiler`; se añadió el import del compilador en los specs. Segundo intento detectó expectativa incorrecta sobre orden lexical; se corrigió el test para reflejar el comportamiento observado. Tercer intento: 3 archivos y 10 tests pasaron. |
| web | H-WEB-05, H-WEB-02, H-WEB-04, H-WEB-06 | `npm run test:coverage` (cwd `web/`), baseline | 10 tests pasaron. Cobertura global 79.26%; `login.component.ts` 96.66% y `dashboard.component.ts` 97.05% de líneas. |
| web | H-WEB-02, H-WEB-03 | `npm run build` (cwd `web/`), baseline | Build correcto; advertencias de CommonJS para `axios` y `lodash/merge`. |
| web | H-WEB-03 | `npm audit --audit-level=moderate` (cwd `web/`) | Exit code 1. 25 vulnerabilidades (10 moderadas, 9 altas, 6 críticas); `axios <=0.33.0` y `lodash <=4.17.23` aparecen como altas. El fix sugerido por npm usa `--force` y queda fuera de las versiones declaradas. |
| web | H-WEB-03 | `npm uninstall lodash` (cwd `web/`) | Falló con `Cannot read properties of null (reading 'children')`; no cambió `package.json` ni `package-lock.json`. El posterior `npm install` de axios no se ejecutó por el fallo previo. |
| web | H-WEB-02, H-WEB-04, H-WEB-05, H-WEB-06 | `npm test -- --reporter=verbose` (cwd `web/`), después del cambio | 4 archivos y 20 tests pasaron antes de añadir los casos finales de ramas de error. |
| web | H-WEB-02, H-WEB-04, H-WEB-05, H-WEB-06 | `npm run test:coverage` (cwd `web/`), validación final | 4 archivos y 23 tests pasaron. Cobertura global 90.07%; `core/` 100%, dashboard 100%, login 100%, utilidad 100% y `environments/environment.ts` 100% de líneas. |
| web | H-WEB-02, H-WEB-04, H-WEB-06 | `npm run build` (cwd `web/`), validación final | Build correcto. Persiste advertencia de CommonJS para `axios`; `lodash/merge` ya no está importado por la aplicación, pero lodash permanece declarado porque no se pudo actualizar el lockfile. |
| web | H-WEB-02, H-WEB-04, H-WEB-05, H-WEB-06 | `npm test -- --reporter=verbose` (cwd `web/`), comprobación final | 4 archivos y 23 tests pasaron tras la limpieza de nombres de las suites. |
| web | H-WEB-02, H-WEB-04, H-WEB-05, H-WEB-06 | `npm run test:coverage` (cwd `web/`), revisión local contra `main` | Repetición durante la revisión: 4 archivos y 23 tests pasaron; cobertura global 90.07%, con los archivos de producción modificados e instrumentados por encima de 85% de líneas. |
| web | H-WEB-02, H-WEB-04, H-WEB-06 | `npm run build` (cwd `web/`), revisión local contra `main` | Build correcto; se mantiene advertencia CommonJS de `axios`. |
| web | H-WEB-03 | `npm audit --audit-level=moderate` (cwd `web/`), revisión local contra `main` | Exit code 1; confirma 25 advisories (10 moderados, 9 altos, 6 críticos). `axios <=0.33.0` y `lodash <=4.17.23` siguen reportados como severidad alta. |
| web | H-WEB-06 | Revisión de diff contra `main`; sin ejecución de prueba específica para status ausente/nulo | Se detectó que `statusLabel` invoca `toUpperCase()` directamente. El test solo cubre valores string; status nulo/ausente queda pendiente de caracterización y corrección. |
| web | H-WEB-05 | `npm test -- --reporter=verbose` (cwd raíz, intento inicial accidental), 2026-10-26 | Falló por `ENOENT` al no existir `package.json` en la raíz; no fue una ejecución válida de pruebas. Se repitió desde `web/` con salida 0. |
| web | H-WEB-05 | `npm test -- --reporter=verbose` (cwd `web/`), ampliación de casos de login y tareas, 2026-10-26 | Exit code 0; 4 archivos y 28 tests pasaron, incluido login seguido de carga del dashboard con la sesión persistida. Incluye servicio de autenticación no disponible, timeout de login, respuesta simulada de token inválido y rechazo por timeout de tareas. Los rechazos fueron simulados con Axios. |
| web | H-WEB-05, H-WEB-06 | `npm run test:coverage` (cwd `web/`), ampliación de pruebas, 2026-10-26 | Exit code 0; 4 archivos y 28 tests pasaron. Cobertura V8: 254/282 líneas globales (90.07%); login, dashboard, `AuthService`, `TasksService` y `SessionService`: 235/235 líneas (100%). No se modificó código de producción en esta tarea; H-WEB-06 sigue pendiente. |

### Resultado por ID y desviaciones

- **H-WEB-01:** aprobado con condición, pero permanece pendiente. No existe en el alcance evidencia de una estrategia de sesión acordada con backend; no se movió el token ni se introdujeron secretos en el frontend.
- **H-WEB-02:** implementado y validado con pruebas y build. HTTP quedó en servicios, sesión en `SessionService` y URLs/timeout/client en `web/src/environments/environment.ts`.
- **H-WEB-03:** no resuelto. La auditoría justificó remediar axios/lodash, pero el gestor de paquetes falló al retirar lodash. No se intentó reescribir el lockfile manualmente ni se ejecutó `npm audit fix --force`; conservar la modificación preexistente de `web/package-lock.json` prevaleció sobre una actualización riesgosa.
- **H-WEB-04:** implementado; mensajes de login se presentan como texto plano, sin `[innerHTML]`.
- **H-WEB-05:** implementado; la última ejecución añadió un flujo login → dashboard y casos de servicio no disponible, timeout y token inválido. Pasaron 28 tests; cobertura V8 global 254/282 líneas (90.07%) y flujos de login/dashboard/sesión 235/235 (100%). Las pruebas no contactan los backends reales.
- **H-WEB-06:** vuelve a pendiente tras la revisión. Se eliminaron los `any` en el código modificado, pero la nueva implementación no conserva la tolerancia a un status ausente/nulo que existía antes (`status || ''`); añadir caracterización y guard antes de cerrar. No se confirmó duplicación, así que no se hizo extracción por ese motivo.
- No se validó con navegador conectado a los backends; las pruebas usan doubles HTTP/localStorage y el build. El contrato observado quedó igual en endpoints, campos del login, query `owner`, encabezado Bearer, navegación y logout.

-- Aprobación Humana

- Nombre: Carla Llano
- Fecha: 2026/10/26
- ID: H-WEB-01, H-WEB-02, H-WEB-03, H-WEB-04, H-WEB-05, H-WEB-06
