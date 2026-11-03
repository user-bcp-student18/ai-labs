## Cambio

**Issue:** no existe Issue en GitHub; el hallazgo es H-API-15 (`HALLAZGOS.md`, sección "Discovery: api").
**Componente:** api. **Rama:** `day1/prompting` (local; sin push ni PR remoto en el Día 1).

**Qué cambió.** `POST /api/requirements` ya no sobrescribe un archivo existente.
- `RequirementService.store` (`api/app/services.py`) crea el archivo en modo exclusivo (`"xb"`) y lanza `FileAlreadyExistsError` si ya existe. Si la escritura falla después de crearlo, elimina el archivo parcial.
- La ruta (`api/app/routes/requirements.py`) traduce ese error a `409 {"detail": "File already exists"}`, sin ruta del servidor.
- Pruebas, `docs/ENDPOINTS.md`, `docs/TESTING.md`, `PLAN.md` y `HALLAZGOS.md` actualizados.

**Por qué.** Comportamiento anterior: dos usuarios que subían el mismo nombre recibían 201 y el segundo reemplazaba el contenido del primero (reproducido con datos ficticios: `alice` y `bob` suben `req.txt`; el contenido final era el de `bob`). Resultado esperado: el archivo existente no se modifica y la subida se rechaza.

**Qué se preservó.** Ruta, método y campo `file`; 201 con `owner`, `fileName`, `storedAt` (`WORKSHOP_UPLOAD_DIR` + nombre) y `size` en una subida con nombre nuevo; 401 `{"detail": "Invalid token"}`; 422 sin `file`; 500 genérico ante fallo interno; esquema `UploadResponse`.

**Cambio de contrato (aprobado por el usuario el 2026-11-03, ver `PLAN.md`):** nuevo 409 en `POST /api/requirements`. Tampoco el mismo usuario puede reemplazar su archivo.

**Qué no se resolvió.**
- H-API-04 (`../`, subdirectorios, extensión, tamaño, `storedAt` con ruta del servidor): sus 2 pruebas siguen `xfail(strict=True)`.
- H-API-01, 02, 03: sin cambios.
- Archivos ya existentes en volúmenes `api-uploads` darán 409 si se reutiliza su nombre (pregunta abierta 6 sin responder).
- Orden respecto a H-API-04 (pregunta abierta 5 sin responder).
- `web` no fue revisado por el agente; el usuario confirmó que no consume `storedAt`/`fileName` (una búsqueda de solo lectura en `web/src` no halló referencias).

**Cómo revertir.** `git revert` de los commits `fix(api): rechazar con 409 ...` y de las pruebas/documentación asociadas. Sin migraciones; los archivos ya subidos no se alteran.

## Comprobación

Entorno: Windows, Python 3.13.15, `api/.venv`.

| # | Comando | Resultado |
|---|---|---|
| 1 | `python tools/lab.py test api` (línea base, antes del cambio) | 134 passed, 6 xfailed; cobertura 100 % (269 sentencias); umbral 85 % alcanzado |
| 2 | `python -m pytest tests/test_endpoints.py -k upload -p no:cacheprovider --no-cov` (cwd `api/`, con la prueba de caracterización `xfail` contra el código antiguo) | 6 passed, 3 xfailed |
| 3 | `python tools/lab.py test api` (tras el cambio) | 138 passed, 6 xfailed; cobertura 100 % (284 sentencias, 0 sin cubrir; 10 ramas, 0 parciales); umbral 85 % alcanzado |

Pruebas nuevas o cambiadas en `api/tests/test_endpoints.py`: mismo nombre del mismo usuario → 409 y primer archivo intacto; mismo nombre de otro usuario → 409 e intacto; 401 sin archivo escrito; 8 subidas concurrentes del mismo nombre → exactamente una con éxito; fallo de escritura simulado → sin archivo parcial y reintento posterior correcto. Se sustituyó `test_upload_same_name_overwrites_previous_file` (que exigía la sobrescritura) con aprobación.

No ejecutado: `mvn verify` (auth), `npm test` (web), Docker/Compose, CodeQL y Dependency Review (solo corren en GitHub). La cobertura se midió sobre todo `api/app/`, no por líneas del diff.

Secciones que sustentan el cambio: `PLAN.md` → "H-API-15"; `docs/ENDPOINTS.md` → `POST /api/requirements` y "Cambios respecto al comportamiento original"; `docs/TESTING.md` → ejecuciones 6 a 8.

## Revisión humana

Pendiente. La persona revisora registra aquí su decisión y motivos. La salida de un agente no sustituye esta revisión.

- [ ] Aprobada / [ ] Cambios solicitados
- Motivos:
