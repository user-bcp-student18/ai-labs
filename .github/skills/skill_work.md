---
name: database-repository-review
description: "Analiza una base de datos a partir del contenido de un repositorio Git y presenta problemas detectables, mejoras y buenas prácticas con evidencia. Úsalo para revisar esquemas, migraciones, consultas SQL, modelos ORM y código de acceso a datos; no modifica ni ejecuta cambios en la base de datos."
---

# Skill: Database Repository Review

## 1) Metadata

- **Skill ID:** database-repository-review
- **Version:** 0.2.0
- **Purpose:** Revisar el diseño y uso de una base de datos definido en un repositorio Git para identificar problemas respaldados por evidencia y recomendar mejoras aplicables siguiendo buenas prácticas.
- **Audience:** Tech Lead, Backend, DBA/Data, QA, DevOps/SRE, Cyber.
- **When to use:** Al solicitar una revisión de BD, auditoría de consultas, revisión de migraciones o recomendaciones de buenas prácticas para la persistencia de un repositorio.
- **When not to use:** Para ejecutar cambios de esquema o datos, operar sobre producción, diagnosticar incidentes activos o certificar rendimiento sin métricas representativas.
- **Sensitive inputs:** No solicitar ni incluir credenciales, cadenas de conexión, tokens, datos reales de clientes ni valores sensibles.
- **Expected output:** Informe Markdown en español con alcance, evidencia, hallazgos priorizados y recomendaciones accionables.

## 2) Inputs

Usa la información disponible en el repositorio y pregunta solo si una decisión del usuario es indispensable:

- **Repositorio y rama revisados:**
- **Componente o dominio de datos en alcance:**
- **Motor y versión de BD:** (si están documentados)
- **Fuentes disponibles:** (DDL, migraciones, modelos ORM, consultas, configuración, tests)
- **Flujos o consultas críticas:** (si se conocen)
- **Volumen, patrón de uso y objetivos de rendimiento:** (si están documentados)
- **Restricciones:** (compatibilidad, contratos de API, stack, cumplimiento)
- **Alcance adicional solicitado:** (si aplica)

No detengas la revisión por falta de datos opcionales: documenta lo que no pudo verificarse como limitación o pregunta abierta.

## 3) Procedure

1. **Confirma el alcance.**
   - Lee las instrucciones aplicables del repositorio y limita la revisión al componente acordado.
   - Inspecciona el estado de Git y los cambios existentes. No sobrescribas, reviertas ni incluyas cambios ajenos a la revisión.
   - Identifica el motor, versión y fuentes de persistencia solo a partir de evidencia del repositorio.
2. **Localiza las fuentes relevantes.**
   - Revisa definiciones de esquema, migraciones, modelos ORM, consultas, repositorios, configuración sin secretos, pruebas y documentación relacionada.
   - Sigue el flujo desde las rutas/servicios que usan persistencia hasta las consultas y el esquema cuando estén presentes.
   - Registra archivos, símbolos, líneas y objetos de BD inspeccionados; diferencia lo revisado de lo no disponible.
3. **Evalúa las categorías aplicables de la sección 3.1.**
   - Verifica problemas concretos y también prácticas correctas observables.
   - Clasifica cada categoría como **Revisada**, **Revisada parcialmente**, **No aplica** o **No verificable**.
4. **Valida la evidencia antes de reportar.**
   - Cada hallazgo debe señalar ubicación exacta y explicar qué evidencia demuestra el problema.
   - Separa hechos observados, inferencias y preguntas abiertas.
   - No infieras volumen, impacto medido, uso de índices en producción ni cumplimiento operacional a partir de nombres o configuración incompleta.
5. **Prioriza y recomienda.**
   - Ordena por severidad y luego por impacto/riesgo.
   - Sugiere cambios mínimos y concretos, indicando compatibilidad, pruebas necesarias, riesgos y reversión cuando aplique.
6. **Entrega el informe.**
   - Devuelve el formato de la sección 3.2. No modifiques código, archivos de configuración ni la base de datos como parte de esta revisión.

## 3.1) Catálogo de revisión

Evalúa cada punto solo cuando exista evidencia o contexto suficiente. Indica **No verificable** en caso contrario.

| Categoría | Buenas prácticas y problemas a revisar |
| --- | --- |
| Esquema y modelado | Nombres consistentes; tipos adecuados; claves primarias; relaciones explícitas; normalización apropiada; desnormalización justificada; evitar columnas multivalor o tablas/campos ambiguos. |
| Integridad de datos | Claves foráneas; `NOT NULL`, `UNIQUE`, `CHECK` y valores por defecto cuando corresponda; reglas de borrado/actualización explícitas; restricciones aplicadas en la BD además de la validación de aplicación. |
| Índices | Índices respaldados por patrones de consulta; columnas de relaciones y filtros; orden de índices compuestos; redundancias potenciales; costo de escritura. No recomendar índices como definitivos sin validar el plan y la carga real. |
| SQL y acceso a datos | Consultas parametrizadas; ausencia de concatenación de entrada no confiable; selección de columnas necesarias; paginación; filtros sargables; joins adecuados; transacciones acotadas; posibles consultas N+1. |
| Rendimiento | Consultas costosas detectables en código; planes `EXPLAIN` existentes; límites y timeouts; pool y concurrencia documentados. No afirmar latencias, saturación o regresiones sin mediciones reproducibles. |
| Seguridad y privacidad | Mínimo privilegio documentado; secretos fuera del código; autorización vinculada a identidad; manejo y minimización de datos sensibles; cifrado, auditoría y retención cuando exista evidencia. No divulgar valores sensibles encontrados. |
| Transacciones y concurrencia | Límites transaccionales claros; rollback ante error; aislamiento adecuado al caso; idempotencia donde se requiera; manejo de actualizaciones concurrentes y deadlocks. |
| Migraciones y despliegue | Cambios de esquema versionados; orden y dependencias claros; compatibilidad entre versiones de aplicación; migraciones repetibles o con rollback/mitigación; evitar cambios manuales no trazables. |
| Pruebas y calidad | Pruebas de repositorio, migraciones, integridad y consultas críticas; datos de prueba aislados/sintéticos; casos de rollback y errores; cobertura según los estándares del repositorio. |
| Operación y resiliencia | Backups y restauraciones documentados/probados; monitorización, alertas, retención, alta disponibilidad y RPO/RTO cuando estén en alcance y documentados. Si no están en el repositorio, reportar como no verificable, no como incumplimiento confirmado. |
| Arquitectura de persistencia | Separación de ruta, servicio y repositorio conforme a las convenciones del proyecto; consultas centralizadas; manejo explícito de errores; configuración externa sin valores secretos. |

## 3.2) Output

Devuelve **solo** el informe Markdown con las siguientes secciones:

1. **Resumen ejecutivo**
   - Estado general basado en evidencia.
   - Conteo de hallazgos por severidad y principales riesgos.
2. **Alcance y método**
   - Repositorio/rama si se conoce, componente y fuentes revisadas.
   - Fuentes excluidas o no disponibles y límites de la revisión.
3. **Inventario de persistencia**
   - Motor/versión si se verificó; esquemas, tablas, migraciones, consultas y módulos revisados.
4. **Hallazgos priorizados**
   - Tabla en el formato de la sección 3.3.
5. **Buenas prácticas observadas**
   - Prácticas correctas con referencia a su evidencia.
6. **Recomendaciones y plan sugerido**
   - Acciones concretas ordenadas como urgente, siguiente iteración o mejora futura.
   - No presentar scripts como ejecutados. Si se incluye SQL ilustrativo, marcarlo como **propuesto; no ejecutado**.
7. **Categorías no verificables / preguntas abiertas**
   - Información necesaria para confirmar o descartar riesgos.
8. **Validación recomendada**
   - Pruebas, métricas o revisión humana necesarias para comprobar cada cambio propuesto.

### 3.3) Formato de hallazgos

| ID | Severidad | Categoría | Ubicación | Evidencia y problema | Impacto/riesgo | Recomendación | Validación |
| --- | --- | --- | --- | --- | --- | --- | --- |
| H-DB-01 | Alta / Media / Baja | Integridad | `ruta/archivo.ext:línea` o `tabla.columna` | Hecho observable y evidencia concreta | Consecuencia posible, sin inventar métricas | Cambio específico y compatible | Prueba o comprobación propuesta |

- Usa IDs consecutivos `H-DB-NN`, salvo que el repositorio tenga una convención de hallazgos propia; en ese caso, respétala.
- **Alta:** evidencia de riesgo significativo de acceso no autorizado, pérdida/corrupción de datos, incumplimiento de integridad o indisponibilidad.
- **Media:** problema funcional o de mantenibilidad con impacto plausible, o riesgo de rendimiento respaldado por consulta/esquema/plan.
- **Baja:** mejora preventiva o de consistencia cuyo impacto es acotado.
- No elevar severidad por especulación. Si el impacto depende de contexto ausente, indícalo y crea una pregunta abierta en vez de afirmar una vulnerabilidad o falla.

## 4) Constraints

- Mantén la revisión en modo **solo lectura**. No conectes a producción ni ejecutes SQL que modifique datos o esquema.
- No leas ni expongas filas con datos personales o sensibles. Para archivos de BD locales, no inspecciones registros; utiliza únicamente metadatos/esquema si es seguro y necesario.
- No ejecutes código del repositorio ni scripts de migración durante la revisión sin autorización explícita.
- No agregues, elimines ni edites archivos; el objetivo es diagnosticar y sugerir, no implementar.
- No inventes motor, versión, índices, cardinalidad, configuración, métricas o estado de backups.
- No reportes como confirmado lo que requiera observabilidad o acceso operacional que no se proporcionó.
- Para cada hallazgo cita una ruta y línea, objeto SQL, migración, prueba o evidencia equivalente. Si no puedes localizar la evidencia, no lo presentes como hallazgo confirmado.
- Conserva contratos y compatibilidad existentes. Señala posibles cambios incompatibles y dependencias de migración.
- No recomiendes silenciar linters, scanners, pruebas o controles de seguridad para ocultar un hallazgo.
- Sigue convenciones e instrucciones del propio repositorio, incluida la nomenclatura de evidencias cuando exista.
- No propongas herramientas nuevas como requisito; si son opcionales, explica su propósito y déjalas como decisión.

## 5) Validation Rules

El informe es válido si:

- Cubre las categorías aplicables del catálogo y marca explícitamente las no verificables o no aplicables.
- Todo hallazgo tiene ID, severidad, ubicación y evidencia concreta.
- Distingue claramente los hechos de las inferencias y preguntas abiertas.
- Cada recomendación es accionable e incluye cómo validarla.
- Los impactos cuantitativos se incluyen solo si hay mediciones o requisitos verificables.
- Incluye prácticas correctas observadas y limitaciones de alcance.
- No incluye secretos, datos reales ni cambios presentados falsamente como ejecutados.

## 6) Evidence

El informe debe enlazar o citar, cuando estén disponibles:

- Archivos de esquema, modelos, consultas y migraciones revisados.
- Pruebas existentes relevantes y su resultado, solo si realmente se ejecutaron.
- Planes `EXPLAIN` y métricas aportadas por el usuario, indicando entorno y fecha.
- Referencias exactas de archivo/línea u objeto para cada hallazgo.

No crear etiquetas Git, PR, commits, evidencias adicionales ni ejecutar pruebas como parte de la revisión, salvo que el usuario lo solicite expresamente.
