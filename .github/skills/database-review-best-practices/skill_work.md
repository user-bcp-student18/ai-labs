---
name: database-review-best-practices
description: Revisa una base de datos (esquema, consultas, índices, seguridad, integridad, rendimiento, operación) y devuelve un informe trazable con hallazgos priorizados, mejoras concretas y buenas prácticas aplicables, sin modificar la BD.
---
# Skill: Database Review -> Mejoras y Buenas Prácticas

## 1) Metadata

- **Skill ID:** database-review-best-practices
- **Version:** 0.1.0
- **Purpose:** Estandarizar la revisión de una base de datos y mostrar, de forma priorizada y verificable, todas las mejoras y buenas prácticas aplicables en modelado, integridad, índices, consultas, seguridad, rendimiento, migraciones y operación.
- **Audience (roles):** Chapter/PO, Tech Lead, Backend, DBA/Data, DevOps/SRE, QA, Cyber
- **When to use:** Antes de liberar cambios de esquema o consultas; al heredar o migrar una BD; en revisiones periódicas de calidad; al preparar una refactorización de la capa de persistencia.
- **When NOT to use:** Incidentes P1 en producción (usar el runbook de incidentes), ejecución de cambios destructivos sin autorización, o revisión sobre datos reales de clientes.
- **Sensitive inputs:** No incluyas datos reales de clientes, credenciales, cadenas de conexión, tokens ni hosts internos no autorizados. Usa esquemas (DDL), datos sintéticos y variables de entorno.
- **Modo de operación:** Solo lectura. La revisión **no** ejecuta `INSERT/UPDATE/DELETE/DROP/ALTER`; los cambios se proponen como scripts sugeridos para revisión humana.
- **Expected output:** Markdown estructurado mediante la sección Output a continuación.

## 2) Inputs

Proporciona la información en este formato:

- **Business context (brief):**
- **Motor y versión:** (SQLite, PostgreSQL, MySQL, SQL Server, Oracle, etc.)
- **Origen del esquema:** (DDL, migraciones, modelos ORM/SQL del repositorio, archivo `.db` local)
- **Consultas o repositorios a revisar:** (rutas de archivos, consultas críticas, endpoints asociados)
- **Volumen y crecimiento esperado:** (filas por tabla, tasa de escritura/lectura)
- **Línea base disponible:** (tiempos de consulta, planes de ejecución, métricas previas)
- **Known technical constraints:** (stack, estándares, compatibilidad con el frontend/contratos existentes)
- **Known risks:** (seguridad, integridad, rendimiento, cumplimiento)
- **Dependencies:** (servicios, equipos, procesos de backup, ETL)
- **Alcance de la revisión:** (todas las categorías o un subconjunto de la sección 3.1)
- **Team Definition of Done (DoD):** (if available)

## 3) Output

Devuelve **solo** un documento Markdown con estas secciones y bullets:

1. **Summary** (estado general, puntaje por categoría y número de hallazgos por severidad)
2. **Scope**
   - Dentro del alcance
   - Fuera del alcance
3. **Supuestos**
4. **Inventario revisado** (tablas, vistas, índices, restricciones, consultas y archivos analizados)
5. **Hallazgos priorizados** (tabla con el formato de la sección 3.2)
6. **Mejoras recomendadas por categoría** (ver catálogo 3.1; indicar para cada categoría: cumple / cumple parcialmente / no cumple / no aplica)
7. **Buenas prácticas ya cumplidas** (reconocer lo correcto, con evidencia)
8. **Scripts o cambios sugeridos** (DDL/SQL propuesto, marcado como *no ejecutado*, con riesgo y plan de reversión)
9. **Riesgos y mitigaciones**
10. **Criterios de aceptación (medibles)**
11. **Plan de validación y evidencia requerida**
    - Pruebas de caracterización de consultas
    - Comparación de planes de ejecución antes/después
    - Verificación de integridad y migración
    - Evidencia a adjuntar (salida de pruebas, planes, checklist actualizado)
12. **Hoja de ruta** (quick wins / corto plazo / mediano plazo)
13. **Tareas sugeridas por rol**
    - Chapter/PO
    - Tech Lead
    - Backend
    - DBA/Data
    - DevOps/SRE
    - QA
    - Cyber
14. **Preguntas abiertas**

### 3.1) Catálogo de revisión (categorías y buenas prácticas de referencia)

| Categoría | Qué revisar |
| --- | --- |
| Modelado y normalización | Entidades y relaciones claras, normalización adecuada (3FN) y desnormalización justificada, tipos de dato correctos y mínimos, nombres consistentes y descriptivos (convención única), sin columnas multivalor ni campos “comodín” |
| Integridad | Claves primarias en todas las tablas, claves foráneas con acción `ON DELETE/UPDATE` definida, `NOT NULL`, `UNIQUE`, `CHECK` y valores por defecto, restricciones en la BD y no solo en la aplicación |
| Índices | Índices en columnas de filtro, unión y ordenamiento; índices compuestos con orden correcto; índices duplicados, redundantes o sin uso; cobertura de claves foráneas; costo en escritura |
| Consultas | Sin `SELECT *`; sin N+1; paginación en listados; filtros sargables (sin funciones sobre columnas indexadas); uso correcto de `JOIN`; transacciones cortas; revisión de planes (`EXPLAIN`) |
| Seguridad | Consultas parametrizadas (sin concatenar SQL), mínimo privilegio por rol/usuario, autorización ligada a la identidad, sin secretos en el código ni en el repositorio, cifrado en tránsito y en reposo, datos sensibles minimizados/enmascarados, auditoría de accesos |
| Rendimiento y escalabilidad | Pool de conexiones dimensionado, consultas lentas identificadas, bloqueos y deadlocks, particionamiento/archivado para tablas grandes, caché donde aplique, estadísticas actualizadas |
| Transacciones y concurrencia | Nivel de aislamiento adecuado, idempotencia en escrituras, manejo de errores con rollback, control de concurrencia optimista cuando aplique |
| Migraciones y versionado | Esquema versionado (Flyway, Liquibase, Alembic u otra herramienta del stack), migraciones repetibles y reversibles, sin cambios manuales en entornos, datos semilla separados de datos reales |
| Operación y resiliencia | Backups automatizados y restauración probada (RPO/RTO definidos), réplicas/alta disponibilidad si aplica, monitoreo y alertas, retención y purga de datos, ambientes separados |
| Calidad de datos y cumplimiento | Datos personales identificados y protegidos, retención definida, trazabilidad de cambios (auditoría, `created_at/updated_at`), datos de prueba sintéticos |
| Capa de acceso a datos | Separación ruta/servicio/repositorio, SQL centralizado en el repositorio, constantes en lugar de valores “mágicos”, pruebas con cobertura ≥ 85% del código modificado |

### 3.2) Formato de hallazgos

| ID | Categoría | Severidad | Ubicación (tabla/consulta/archivo) | Hallazgo | Impacto | Mejora recomendada | Esfuerzo | Evidencia |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H-DB-01 | Índices | Alta / Media / Baja | `tabla.columna` | Descripción verificable | Riesgo o costo | Acción concreta | S / M / L | Plan de ejecución, DDL, salida de prueba |

- Severidad: **Alta** (riesgo de seguridad, pérdida o corrupción de datos, caída), **Media** (degradación de rendimiento o mantenibilidad), **Baja** (convención o mejora menor).
- Usa IDs `H-DB-NN`, consecutivos y únicos.

## 4) Constraints

- No inventes tablas, columnas, volúmenes ni métricas: si falta información, inclúyela bajo **Preguntas abiertas**.
- Todo hallazgo debe citar evidencia concreta (tabla, columna, consulta, archivo y línea o plan de ejecución); sin evidencia no se reporta como hallazgo, se reporta como pregunta abierta.
- No ejecutes sentencias que modifiquen la BD ni accedas a datos reales; trabaja sobre el esquema, consultas y copias sintéticas/aisladas.
- No propongas herramientas fuera del stack permitido; si una mejora requiere una herramienta no aprobada, indícalo como decisión pendiente.
- No conviertas un hallazgo de seguridad en una exclusión o supresión de scanner; propón la corrección.
- Conserva los contratos existentes (endpoints, formatos de respuesta): toda mejora debe indicar su impacto de compatibilidad.
- Los criterios de aceptación deben ser verificables y numéricos (por ejemplo, "la consulta X usa índice y p95 < 50 ms con 10 000 filas sintéticas"); no escribas “mejorar el rendimiento” sin una métrica.
- No incluyas datos sensibles ni secretos.
- Mantén la salida usable: resumen en 1 página y detalle ordenado por severidad.

## 5) Validation Rules

La salida es válida si:

- Incluye todas las secciones definidas en Output.
- Evalúa cada categoría del catálogo 3.1 (o indica por qué no aplica).
- Todos los hallazgos siguen el formato 3.2, con ID `H-DB-NN`, severidad y evidencia.
- Incluye al menos 3 criterios de aceptación medibles.
- Incluye al menos 2 riesgos con mitigaciones.
- Incluye al menos un script o cambio sugerido marcado como *no ejecutado*, con plan de reversión, o explica por qué no hay cambios.
- Incluye la sección de buenas prácticas ya cumplidas (aunque sea vacía con justificación).
- Tiene al menos 3 tareas para cada rol central: Tech Lead, Backend y DBA/Data, o explica por qué un rol no aplica.
- No contiene datos sensibles ni secretos.
- No contiene supuestos no declarados.

## 6) Evidence

Adjunta o referencia estos elementos en el PR o entrega:

- `skill_work.md` versionado.
- `examples/input.sample.md`.
- `examples/output.sample.md`.
- Informe de hallazgos (`H-DB-NN`) con evidencia: DDL revisado, planes de ejecución (`EXPLAIN`) y salida de pruebas.
- Tag de versión para el Skill, como `skill-database-review-v0.1.0`.
