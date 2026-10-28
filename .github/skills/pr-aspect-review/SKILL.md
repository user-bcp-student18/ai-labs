---
name: pr-aspect-review
description: Revisa un Pull Request desde un único aspecto concreto (pruebas, seguridad o compatibilidad) y entrega hallazgos con evidencia, severidad y recomendación. Úsalo cuando se pida revisar un PR enfocado en uno de esos aspectos.
---

# PR Aspect Review

## Entradas

```text
PR: número o URL (obligatorio)
aspecto: tests | security | compatibility (obligatorio)
componente: auth | api | web (opcional; limita el alcance)
```

Si falta el aspecto, pregunta cuál usar. No revises los tres aspectos a la vez salvo que se pida explícitamente.

## Precondiciones

- Estás en la raíz de `ai-labs`, el único repositorio Git.
- `gh` está autenticado para leer el PR.
- El PR existe y su diff es accesible. Si no, detente y repórtalo.

## Procedimiento

1. Lee la plantilla `.github/pull_request_template.md` (y `.github/PULL_REQUEST_TEMPLATE/` si existe) para conocer lo que el autor declaró validar.
2. Obtén metadatos y diff:
   ```text
   gh pr view <PR> --json number,title,body,baseRefName,headRefName,files,author
   gh pr diff <PR>
   ```
3. Limita el análisis a los archivos del componente indicado y a los archivos relacionados con el aspecto. No leas ni modifiques componentes fuera del alcance acordado.
4. Aplica la checklist del aspecto elegido (sección siguiente).
5. Verifica cada hallazgo contra el código real: abre el archivo en la rama del PR y confirma la línea antes de reportarlo.
6. Ejecuta las pruebas solo si el aspecto lo requiere y el comando es documentado. Usa `python tools/lab.py test <componente>` desde la raíz. Registra el comando y su resultado exacto (pasó o falló). Si no las ejecutaste, dilo.
7. Entrega el informe con el formato de salida.

## Checklist por aspecto

### tests

- ¿El cambio tiene pruebas nuevas o actualizadas para el comportamiento modificado?
- ¿Las pruebas afirman comportamiento (no solo que el código se ejecuta)?
- ¿Se eliminaron, saltaron (`skip`, `xit`, `@Disabled`) o debilitaron pruebas existentes sin justificación?
- ¿Hay pruebas de caracterización antes de refactorizar?
- ¿La cobertura del código modificado llega a la meta del componente (85 % o más)?
- ¿Se cubren casos límite: entradas vacías, nulos, errores, límites de tamaño?
- ¿Las pruebas son deterministas (sin dependencias de hora, red o orden)?

### security

- ¿Hay secretos, tokens, contraseñas o URLs internas en el diff?
- ¿Las consultas SQL están parametrizadas?
- ¿La autorización está ligada a la identidad del usuario autenticado, no a parámetros enviados por el cliente?
- ¿Se validan nombre, tamaño y extensión de archivos subidos?
- ¿Se silencian alertas (`# noqa`, exclusiones de CodeQL, Dependency Review o JaCoCo, supresiones de scanner)?
- ¿Se agregan dependencias nuevas? Verifica que estén justificadas y sin CVE conocidos.
- ¿Los errores exponen trazas o datos internos?
- ¿CORS, cabeceras o configuración de seguridad se relajaron?

### compatibility

- ¿Se conservan los endpoints y sus formatos de request/response (por ejemplo `POST /auth/login`, `/api/tasks`)?
- ¿Cambian nombres de campos JSON, códigos de estado o tipos de datos consumidos por el frontend?
- ¿Cambian versiones de runtime, framework o dependencias de forma incompatible?
- ¿Se modifican claves de `localStorage`, variables de entorno o rutas de configuración sin migración?
- ¿Los cambios de esquema de datos tienen una ruta de migración o son retrocompatibles?
- ¿El cambio puede revertirse sin pérdida de datos?

## Clasificación de severidad

```text
CRÍTICO  : explotable o rompe producción/contrato sin mitigación
ALTO     : riesgo funcional o de seguridad significativo
MEDIO    : deuda o riesgo acotado con mitigación parcial
BAJO     : mejora o estilo sin impacto funcional
```

Asigna confianza (alta, media, baja) a cada hallazgo. Si la confianza es baja, dilo y explica qué falta verificar.

## Formato de salida

```text
# Revisión PR #<número> — aspecto: <aspecto>

## Resumen
<2-3 líneas: qué hace el PR y veredicto: aprobar | aprobar con cambios | no aprobar>

## Hallazgos
| # | Severidad | Confianza | Archivo:línea | Hallazgo | Recomendación |

## Evidencia de pruebas
- Comando: <exacto>  Resultado: <pasó | falló | no ejecutado>

## Qué no se revisó
<alcance excluido y por qué>

## Preguntas al autor
<lista corta, solo si son necesarias>
```

Si no hay hallazgos, dilo explícitamente en la sección Hallazgos.

## Reglas

- Revisa solo el aspecto pedido; los hallazgos de otros aspectos van en "Qué no se revisó" como observación breve, sin análisis profundo.
- No inventes resultados de pruebas ni líneas inexistentes.
- No publiques comentarios en el PR, no apruebes, no hagas merge y no hagas push sin confirmación explícita del usuario.
- No silencies ni recomiendes silenciar alertas de seguridad o quality gates.
- No incluyas secretos ni datos reales en el informe; si encuentras uno, indica archivo y línea y marca el valor como redactado.
- No modifiques código durante la revisión.
- Mantén el informe corto: prioriza los hallazgos de severidad alta y crítica.
