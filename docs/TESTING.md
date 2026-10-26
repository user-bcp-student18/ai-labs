# Pruebas del componente web

**Alcance:** login y consulta de tareas del frontend Angular. Los tests ejercitan componentes, servicios, sesión y manejo de errores con Axios simulado y almacenamiento en memoria; no llaman a los backends.

## Casos y resultados esperados

| flujo | caso | tipo | resultado esperado |
|---|---|---|---|
| Login | Credenciales válidas; recibe token y usuario | Camino feliz | Envía `username`, `password` y `client`; guarda la sesión y navega a `/dashboard`. |
| Tareas | Token presente y respuesta con tareas válidas | Camino feliz | Solicita las tareas con `owner` y encabezado Bearer, oculta las archivadas, ordena las restantes y apaga la carga. |
| Login → tareas | Login válido seguido de carga del dashboard desde la sesión guardada | Camino feliz integrado | El token y usuario guardados por login se reutilizan para solicitar tareas; la tarea aparece en el dashboard. |
| Login | Username vacío o solo espacios | Borde | No envía HTTP y muestra `Ingrese un usuario.` |
| Login | Password vacío o solo espacios | Borde | No envía HTTP y muestra `Ingrese una contraseña.` |
| Login | Respuesta exitosa sin token | Borde | Muestra `El backend respondió sin token.`, no guarda sesión y no navega. |
| Tareas | No hay token en sesión | Borde | No solicita tareas y navega a `/login`. |
| Login | Servicio de autenticación no disponible (error de red simulado) | Error | Muestra `No se pudo autenticar a student.`, libera el indicador de actividad y no crea sesión. |
| Login | Solicitud agotó el timeout configurado de 5000 ms (rechazo simulado) | Error | Muestra el mensaje genérico de autenticación, libera el indicador de actividad y no crea sesión. |
| Login | Rechazo HTTP con detalle de backend (representa fallo de credenciales; el status backend no está acordado) | Error | No expone el detalle recibido y muestra el mensaje genérico de autenticación. |
| Tareas | Token rechazado por el servidor (401 simulado; status exacto pendiente de contrato backend) | Error | Muestra el `detail` recibido, apaga la carga, conserva la sesión y no redirige automáticamente, conforme al comportamiento actual. |
| Tareas | Axios rechaza por timeout (sin timeout propio configurado en `TasksService`) | Error | Muestra el mensaje del error y apaga la carga. El test simula el rechazo; no afirma un límite temporal para este endpoint. |

## Código de los tests

Los siguientes casos están implementados en los archivos de prueba existentes. Los cuerpos reproducidos corresponden a las pruebas que cubren los escenarios de la tabla.

### `web/src/app/login/login.component.spec.ts`

```typescript
it('posts credentials and persists the returned session before navigating', async () => {
  vi.mocked(axios.post).mockResolvedValue({
    data: { token: 'test-token', user: { username: 'student' } }
  });

  await component.login();

  expect(axios.post).toHaveBeenCalledWith(
    'http://localhost:8080/auth/login',
    { username: 'student', password: 'Workshop123!', client: 'angular-workshop' },
    { timeout: 5000 }
  );
  expect(storage.getItem('workshop_token')).toBe('test-token');
  expect(JSON.parse(storage.getItem('workshop_user') ?? '{}')).toEqual({ username: 'student' });
  expect(navigate).toHaveBeenCalledWith(['/dashboard']);
  expect(component.busy).toBe(false);
});

it('does not submit a blank username', async () => {
  component.username = '  ';

  await component.login();

  expect(axios.post).not.toHaveBeenCalled();
  expect(component.message).toContain('Ingrese un usuario.');
});

it('does not submit a blank password', async () => {
  component.password = '  ';

  await component.login();

  expect(axios.post).not.toHaveBeenCalled();
  expect(component.message).toContain('Ingrese una contraseña.');
});

it('shows a message when the response does not contain a token', async () => {
  vi.mocked(axios.post).mockResolvedValue({ data: {} });

  await component.login();

  expect(component.message).toContain('El backend respondió sin token.');
  expect(navigate).not.toHaveBeenCalled();
});

it('shows a plain-text authentication error without exposing backend details', async () => {
  vi.mocked(axios.post).mockRejectedValue({
    response: { data: { message: 'Credenciales inválidas' } }
  });

  await component.login();

  expect(component.message).toBe('No se pudo autenticar a student.');
  expect(component.message).not.toContain('<');
  expect(component.busy).toBe(false);
});

it('shows the generic authentication message when the service is unavailable', async () => {
  vi.mocked(axios.post).mockRejectedValue({
    code: 'ERR_NETWORK',
    message: 'Network Error'
  });

  await component.login();

  expect(component.message).toBe('No se pudo autenticar a student.');
  expect(component.busy).toBe(false);
  expect(storage.getItem('workshop_token')).toBeNull();
  expect(navigate).not.toHaveBeenCalled();
});

it('shows the generic authentication message when the login request times out', async () => {
  vi.mocked(axios.post).mockRejectedValue({
    code: 'ECONNABORTED',
    message: 'timeout of 5000ms exceeded'
  });

  await component.login();

  expect(component.message).toBe('No se pudo autenticar a student.');
  expect(component.busy).toBe(false);
  expect(storage.getItem('workshop_token')).toBeNull();
  expect(navigate).not.toHaveBeenCalled();
});
```

### `web/src/app/dashboard/dashboard.component.spec.ts`

```typescript
it('redirects to login when the stored token is missing', async () => {
  await component.ngOnInit();

  expect(navigate).toHaveBeenCalledWith(['/login']);
  expect(axios.get).not.toHaveBeenCalled();
});

it('loads tasks with the stored owner and bearer token, filters and sorts them', async () => {
  storage.setItem('workshop_token', 'test-token');
  storage.setItem('workshop_user', JSON.stringify({ username: 'student' }));
  vi.mocked(axios.get).mockResolvedValue({
    data: [
      { title: 'Low', status: 'TODO', priority: 'low', owner: 'student' },
      { title: 'Archived', status: 'ARCHIVED', priority: 'urgent', owner: 'student' },
      { title: 'High', status: 'IN_PROGRESS', priority: 'high', owner: 'student' }
    ]
  });

  await component.ngOnInit();

  expect(axios.get).toHaveBeenCalledWith(
    'http://localhost:8000/api/tasks',
    { params: { owner: 'student' }, headers: { Authorization: 'Bearer test-token' } }
  );
  expect(component.tasks).toHaveLength(3);
  expect(component.visibleTasks.map((task) => task.title)).toEqual(['Low', 'High']);
  expect(component.visibleTasks[0].label).toBe('LOW · STUDENT');
  expect(component.loading).toBe(false);
  expect(component.error).toBe('');
});

it('logs in and loads tasks using the persisted session', async () => {
  vi.mocked(axios.post).mockResolvedValue({
    data: { token: 'test-token', user: { username: 'student' } }
  });
  const loginNavigate = vi.fn().mockResolvedValue(true);
  const loginComponent = new LoginComponent(
    { navigate: loginNavigate } as unknown as Router,
    new AuthService(),
    new SessionService()
  );
  loginComponent.username = 'student';
  loginComponent.password = 'Workshop123!';
  vi.mocked(axios.get).mockResolvedValue({
    data: [{ title: 'First task', description: 'Example task', status: 'TODO', owner: 'student' }]
  });

  await loginComponent.login();
  await component.ngOnInit();

  expect(storage.getItem('workshop_token')).toBe('test-token');
  expect(loginNavigate).toHaveBeenCalledWith(['/dashboard']);
  expect(axios.get).toHaveBeenCalledWith(
    'http://localhost:8000/api/tasks',
    { params: { owner: 'student' }, headers: { Authorization: 'Bearer test-token' } }
  );
  expect(component.visibleTasks.map((task) => task.title)).toEqual(['First task']);
  expect(component.loading).toBe(false);
});

it('shows an invalid-token response without clearing the session or redirecting', async () => {
  storage.setItem('workshop_token', 'invalid-token');
  storage.setItem('workshop_user', JSON.stringify({ username: 'student' }));
  vi.mocked(axios.get).mockRejectedValue({
    response: { status: 401, data: { detail: 'Invalid token' } }
  });

  await component.ngOnInit();

  expect(component.error).toBe('Invalid token');
  expect(component.loading).toBe(false);
  expect(storage.getItem('workshop_token')).toBe('invalid-token');
  expect(navigate).not.toHaveBeenCalled();
});

it('shows a task request timeout message and clears loading', async () => {
  storage.setItem('workshop_token', 'test-token');
  storage.setItem('workshop_user', JSON.stringify({ username: 'student' }));
  vi.mocked(axios.get).mockRejectedValue({
    code: 'ECONNABORTED',
    message: 'timeout of 5000ms exceeded'
  });

  await component.ngOnInit();

  expect(component.error).toBe('timeout of 5000ms exceeded');
  expect(component.loading).toBe(false);
});
```

## Ejecuciones y cobertura

Las pruebas se ejecutaron desde `web/`, como requiere el proyecto.

| Componente | IDs | Comando y directorio | Código de salida | Resultado |
|---|---|---|---:|---|
| web | H-WEB-05 | `npm test -- --reporter=verbose` (`web/`) | 0 | 4 archivos de prueba pasaron; 28 tests pasaron, 0 fallaron, incluido login → dashboard con sesión compartida. |
| web | H-WEB-05 | `npm run test:coverage` (`web/`) | 0 | 4 archivos de prueba pasaron; 28 tests pasaron, 0 fallaron. Reporte de cobertura V8 en `web/coverage/`. |

**Medición de cobertura (V8, reporte de líneas/statement de Vitest):**

- **Código de producción de los flujos probados:** login, dashboard, `AuthService`, `TasksService` y `SessionService`: 235/235 líneas ejecutables cubiertas = **100%**. Desglose: login 52/52, dashboard 81/81, `AuthService` 16/16, `TasksService` 13/13, `SessionService` 73/73.
- **Cobertura global del componente web:** 254/282 líneas ejecutables cubiertas = **90.07%**. Las 28 líneas no cubiertas incluyen puntos de entrada y componentes que no forman parte de estos flujos.
- **Numerador/denominador y método:** el numerador es la cantidad de líneas cubiertas y el denominador el total de líneas ejecutables instrumentadas por el provider V8; porcentaje = numerador / denominador × 100. Datos leídos del reporte JSON `web/coverage/coverage-summary.json`.
- En esta tarea solo se modificaron archivos de test y documentación; no se modificó código de producción. Por ello, una métrica de “cobertura de líneas modificadas de producción” no tiene denominador para este cambio. Se informa además la cobertura de las líneas de producción de los flujos, sin presentarla como cobertura de los propios archivos de test.

## Fallos, pendientes y pruebas propuestas

### Fallos

- La primera ejecución de `npm test -- --reporter=verbose` se lanzó por error desde la raíz, donde no existe `package.json`: npm informó `ENOENT` y el proceso devolvió código `-4058` en PowerShell. No fue una ejecución válida de la suite; se repitió desde `web/` y terminó con código 0.

### Pendientes y límites

- Los tests usan dobles de Axios y almacenamiento en memoria; no verifican conectividad, códigos o cuerpos de un backend real. Los errores de red, timeout y 401 son rechazos/respuestas simulados, no resultados observados del servidor.
- `GET /api/tasks` no configura timeout propio. Su prueba verifica cómo la UI presenta un rechazo de Axios con mensaje de timeout, no que el endpoint tenga un límite de 5000 ms.
- **Defecto independiente H-WEB-06:** una tarea con `status` nulo o ausente puede provocar un error al renderizar porque `statusLabel()` invoca `toUpperCase()` directamente (`web/src/app/dashboard/dashboard.component.ts:40-41`; uso en `web/src/app/dashboard/dashboard.component.html:21`). No se añadió un test que ajuste o normalice este comportamiento; la corrección y su prueba quedan pendientes. La respuesta de éxito con estados válidos sí está cubierta.
- En el chequeo de herramientas, Node.js estaba disponible (`v26.9.0`, npm `11.19.1`); `docker` no estaba disponible en PATH. Docker no es requisito de estos tests unitarios con dobles. No se ejecutaron pruebas de navegador ni integración con servicios reales.

### Pruebas propuestas no ejecutadas

- Ejecutar el flujo login → dashboard con los servicios locales/backend disponibles para validar el contrato entre componentes.
- Cuando se corrija H-WEB-06, añadir una prueba específica de tarea con `status` ausente/nulo y verificar una salida segura; hasta entonces, ese caso sigue reportado como defecto y no como test aprobado.

## Documentos consultados

- `README.md` — comandos y reglas de pruebas del laboratorio.
- `RETO.md` — contexto del componente web y objetivo de pruebas.
- `docs/GOOD_PRACTICES.md` — convenciones de pruebas y comportamiento web.
- `docs/ENDPOINTS.md` — payloads y casos de error documentados.
- `HALLAZGOS.md` — estado de H-WEB-05 y defecto H-WEB-06.
- `PLAN.md` — historial de aprobaciones y ejecuciones anteriores.
- Código de pruebas bajo `web/src/app/` y configuración `web/vitest.config.ts`.
