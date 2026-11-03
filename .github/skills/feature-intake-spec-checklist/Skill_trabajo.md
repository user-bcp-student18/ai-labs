```skill

---
name: resource-performance-validation
description: Estandariza nuevas formas de validar el rendimiento de recursos de BD, microservicios y App Services mediante SLIs/SLOs, pruebas de carga, observabilidad, análisis de consultas y gates de regresión, generando un paquete mínimo trazable con evidencia medible.
---
# Skill: Resource Performance Validation (BD, Microservicios, App Services)

## 1) Metadata

- **Skill ID:** resource-performance-validation
- **Version:** 0.1.0
- **Purpose:** Estandarizar cómo se valida el rendimiento de recursos de base de datos, microservicios y App Services con enfoques modernos (SLO-driven, pruebas de carga y resiliencia, observabilidad, profiling y gates de regresión en CI), generando un plan trazable con métricas, umbrales y evidencia.
- **Audience (roles):** Chapter/PO, Tech Lead, Backend, DBA/Data, DevOps/SRE, QA, Cyber
- **When to use:** Antes de liberar un cambio con impacto en latencia, throughput, consumo de recursos o costo; al dimensionar o migrar un recurso (BD, servicio, App Service); al definir o revisar SLOs.
- **When NOT to use:** Incidentes P1 en producción (usar el runbook de incidentes), cambios sin impacto en rendimiento (typos, documentación) o pruebas contra producción sin autorización.
- **Sensitive inputs:** No incluyas datos reales de clientes, credenciales, cadenas de conexión, tokens ni URLs/hosts internos no autorizados. Usa datos sintéticos y variables de entorno.
- **Expected output:** Markdown estructurado mediante la sección Output a continuación.

## 2) Inputs

Proporciona la información en este formato:

- **Business context (brief):**
- **Recurso(s) a validar:** (BD: motor/versión y tamaño; microservicio; App Service: plan/SKU, instancias)
- **Flujo crítico o endpoint/consulta objetivo:**
- **Carga esperada:** (usuarios concurrentes, RPS, picos, estacionalidad)
- **SLIs/SLOs actuales o deseados:** (latencia p95/p99, tasa de error, disponibilidad)
- **Línea base disponible:** (métricas previas, resultados de pruebas anteriores)
- **Known technical constraints:** (stack, standards, límites de pool/CPU/memoria, cuotas)
- **Known risks:** (saturación, bloqueos, costo, estabilidad, seguridad)
- **Dependencies:** (servicios, colas, caches, equipos, datos de prueba)
- **Entorno de prueba:** (local, QA, preproducción) y herramientas de observabilidad disponibles
- **Team Definition of Done (DoD):** (if available)

## 3) Output

Devuelve **solo** un documento Markdown con estas secciones y bullets:

1. **Summary**
2. **Scope**
   - Dentro del alcance
   - Fuera del alcance
3. **Supuestos**
4. **SLIs / SLOs y umbrales**
   - Métricas por recurso (ver sección 3.1)
   - Línea base y umbral de regresión permitido
5. **Estrategia de validación por tipo de recurso**
   - Base de datos
   - Microservicios
   - App Services
6. **Técnicas de validación seleccionadas** (justificar cada una)
   - Pruebas de carga, estrés, picos (spike) y resistencia (soak)
   - Análisis de planes de ejecución y consultas lentas
   - Observabilidad y trazas distribuidas
   - Profiling continuo o puntual
   - Pruebas de resiliencia y degradación controlada
   - Pruebas sintéticas / monitoreo de disponibilidad
   - Gates de regresión de rendimiento en CI/CD
   - Eficiencia y costo por transacción
7. **Riesgos y mitigaciones**
8. **Criterios de aceptación (medibles)**
9. **Plan de ejecución y evidencia requerida** (qué correr, con qué datos, qué adjuntar)
10. **Tareas sugeridas por rol**
    - Chapter/PO
    - Tech Lead
    - Backend
    - DBA/Data
    - DevOps/SRE
    - QA
    - Cyber
11. **Preguntas abiertas**

### 3.1) Catálogo de métricas de referencia

| Recurso | Métricas clave |
| --- | --- |
| Base de datos | Latencia de consultas p95/p99, consultas lentas, uso de índices vs. full scans, locks/deadlocks, conexiones activas vs. máximo del pool, CPU/IO/memoria, tamaño y crecimiento, replicación/lag |
| Microservicio | Método RED (Rate, Errors, Duration), latencia p95/p99 por endpoint, saturación de hilos/pool, tiempo de respuesta de dependencias, reintentos y timeouts, circuit breakers abiertos |
| App Service | CPU y memoria por instancia, tiempos de arranque en frío, cola de solicitudes, comportamiento de autoscaling, errores HTTP 5xx, uso de conexiones salientes, método USE (Utilization, Saturation, Errors) |

## 4) Constraints

- No inventes requisitos ni métricas: si falta información, inclúyela bajo **Preguntas abiertas**.
- No propongas herramientas fuera del stack permitido; si una técnica requiere una herramienta no aprobada, indícalo como decisión pendiente.
- No incluyas datos sensibles ni secretos; las pruebas usan datos sintéticos y entornos aislados.
- Los criterios de aceptación deben ser verificables y numéricos (por ejemplo, "p95 < 300 ms a 100 RPS durante 10 min con error < 1%"); no escribas “mejorar el rendimiento” sin una métrica.
- Toda comparación debe referirse a una línea base explícita; si no existe, el primer entregable es establecerla.
- Las pruebas de carga, estrés o caos no se ejecutan contra producción sin autorización documentada.
- El plan debe incluir al menos un elemento de evidencia concreto, como reporte de la prueba, captura de dashboard, plan de ejecución o checklist actualizado.
- Mantén la salida en un máximo de 1-2 páginas para que siga siendo usable.

## 5) Validation Rules

La salida es válida si:

- Incluye todas las secciones definidas en Output.
- Define al menos 3 criterios de aceptación medibles con umbral, carga y duración.
- Cubre cada tipo de recurso involucrado (BD, microservicio, App Service) o explica por qué uno no aplica.
- Incluye al menos 3 técnicas de validación de la sección 3, cada una con justificación.
- Define línea base y umbral de regresión permitido.
- Tiene al menos 3 tareas para cada rol central: Tech Lead, Backend y QA, o explica por qué un rol no aplica.
- Incluye al menos 2 riesgos con mitigaciones.
- No contiene datos sensibles ni secretos.
- No contiene supuestos no declarados.

## 6) Evidence

Adjunta o referencia estos elementos en el PR o entrega:

- `SKILL.md` versionado.
- `examples/input.sample.md`.
- `examples/output.sample.md`.
- Resultados de las pruebas (reporte de carga, planes de ejecución, dashboards o trazas) con fecha, entorno y versión del recurso.
- Tag de versión para el Skill, como `skill-resource-performance-v0.1.0`.
```
