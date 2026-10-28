---
name: revision-pr-autorizacion
description: 'Revisa localmente un pull request mediante MCP buscando defectos y riesgos de autorizacion de acceso a recursos. Usar para una revision de seguridad de PR con evidencia del diff y referencias fijadas por SHA, sin publicar una review.'
argument-hint: 'URL del PR y, opcionalmente, ruta para guardar la revision local'
---
# Revision local de autorizacion en un PR

## Alcance y criterio

los cambios no deben permitir que un actor acceda o modifique un recurso sin la comprobacion de permisos, propiedad o aislamiento entre tenants que corresponda. Considera tambien eliminaciones o cambios en controles existentes. No revises otros aspectos de seguridad, pruebas en general ni compatibilidad. No supongas que una comprobacion falta sin verificar el contexto necesario.

Incluye en la revision lo de Clean Code, asegurando que el codigo sea legible, mantenible y siga buenas practicas de estructura y nomenclatura. Esto implica revisar la claridad de los nombres de variables y funciones, la organizacion del codigo, la consistencia en el estilo y la ausencia de codigo duplicado o innecesario. Ademas, verifica que los cambios no introduzcan complejidad innecesaria y que el flujo del codigo sea facil de seguir. Registra cualquier observacion relacionada con la legibilidad, mantenibilidad o adherencia a buenas practicas de Clean Code junto con las observaciones de autorizacion.

incluye en los Test el l patrón AAA (Arrange-Act-Assert u Organizar, Actuar y Afirmar) es un estándar en la industria para estructurar pruebas unitarias y de software de forma clara y mantenible y asegúrate de que cada prueba siga esta estructura para mejorar la legibilidad y la comprensión del flujo de la prueba. Registra cualquier observación relacionada con la adherencia al patrón AAA junto con las observaciones de autorizacion y Clean Code.

## Entrada

- URL del PR. Si falta, solicitala antes de continuar.

## Salida

Ruta opcional para el informe local. Por defecto usa `revision-pr-<numero>.md` en la raiz del workspace. Si ya existe, no lo sobrescribas: solicita otra ruta o usa un nombre disponible.

## Procedimiento

1. Utiliza las herramientas MCP disponibles para consultar el PR y su diff. Obtiene la URL, el repositorio, el numero, los nombres y los SHA completos de las referencias base y cabeza. No uses el checkout local como sustituto del PR o del diff consultados mediante MCP.
2. Recupera el diff completo correspondiente a esos SHA, incluyendo todas las paginas. Comprueba que las respuestas identifican la misma base y cabeza; si el PR cambia durante la consulta, vuelve a obtener sus referencias y el diff hasta tener una version consistente. No mezcles datos de versiones distintas.
3. Examina los cambios relevantes para el criterio, incluidos controles eliminados y rutas de acceso a recursos. Para confirmar un hallazgo, consulta mediante MCP el contexto adicional necesario en el SHA de cabeza; cuando sea relevante para una eliminacion o comparacion, consulta tambien el SHA de base. No uses el contenido actual de una rama como si fuera el de un SHA fijado.
4. Ancla cada observacion a una linea o fragmento concreto del diff: archivo, lado base o cabeza, numero de linea y fragmento breve. Incluye un enlace directo a la linea del diff si MCP lo proporciona; de lo contrario, proporciona la URL del PR, los SHA y los datos de localizacion anteriores. Explica la relacion entre esa evidencia y el posible acceso no autorizado.
5. Clasifica cada observacion como **defecto demostrado** solo si el diff y el contexto fijado acreditan la condicion y sus consecuencias; en caso contrario, como **riesgo por confirmar**. Indica una prueba o comprobacion concreta que reproduzca o descarte cada observacion, con actor, recurso y resultado esperado cuando corresponda. Registra como ejecutada una prueba solo si realmente se ejecuto, con su comando y resultado; de lo contrario, marcala como pendiente.
6. Escribe el informe local con el formato siguiente. Si no hay observaciones, indica expresamente que no se encontraron y describe que controles y cambios se comprobaron. Indica tambien el contexto o las comprobaciones que no pudieron revisarse.
7. No publiques comentarios, revisiones ni aprobaciones en el PR. El informe no es una aprobacion ni una evaluacion general del PR.

Si MCP no esta disponible, el PR o el diff no son accesibles, falta alguna pagina, no pueden fijarse o relacionarse los SHA con el diff, o no puede obtenerse el contexto necesario, explica la limitacion en el informe y no presentes la revision como completa. No inventes evidencia ni resultados; para contexto faltante, registra solo riesgos sustentados en el diff y especifica que falta confirmar.

## Formato del informe

```markdown
# Revision local de autorizacion

- PR: <URL>
- Repositorio y numero: <repositorio>, #<numero>
- Base: <nombre de referencia> @ <SHA completo>
- Cabeza: <nombre de referencia> @ <SHA completo>
- Criterio: autorizacion de acceso y modificacion de recursos.
- Cobertura y limitaciones: <archivos o cambios revisados; diff completo o incompleto; contexto no disponible>

## Observaciones

### <titulo> — <defecto demostrado | riesgo por confirmar>
- Evidencia del diff: <archivo>, <base/cabeza>, linea <numero>, `<fragmento>`; <enlace directo si disponible>.
- Analisis: <condicion, actor, recurso, consecuencia y contexto fijado pertinente>.
- Confirmacion: <prueba o comprobacion concreta y resultado esperado>.
- Estado de la prueba: <pendiente | ejecutada: comando y resultado>.

## Comprobaciones realizadas

<Controles y cambios examinados, incluso si no hay observaciones; pruebas ejecutadas o pendientes.>

Revision local limitada al criterio indicado; no constituye una aprobacion del PR.
```
