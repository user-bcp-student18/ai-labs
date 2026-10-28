
La revisión local de autorización del PR se considera finalizada solo si se cumplen todos los criterios de salida obligatorios. Si alguno no se cumple, indícalo explícitamente en el informe como limitación y no presentes la revisión como completa.

Criterios obligatorios:

1. Informe escrito: el archivo `revision-pr-<numero>.md` (o la ruta indicada) existe en la ubicación acordada y no sobrescribió un informe previo.
2. Cabecera completa: el informe incluye PR (URL), repositorio y número, base y cabeza con nombre de referencia y SHA completo, criterio y cobertura/limitaciones.
3. Diff fijado: las referencias base y cabeza son consistentes con el diff revisado. No se mezclaron datos de versiones distintas y, si el PR cambió durante la consulta, se volvió a obtener todo.
4. Cobertura completa o limitada: el diff se revisó en su totalidad (todas las páginas) o la sección de cobertura declara explícitamente qué faltó.
5. Anclaje de cada observación: cada observación indica archivo, lado (base o cabeza), número de línea y fragmento breve, y enlaza al diff si MCP lo proporciona; si no, incluye URL del PR y SHA.
6. Clasificación correcta: cada observación se marca como **defecto demostrado** solo si el diff y el contexto fijado acreditan condición y consecuencia; en otro caso, como **riesgo por confirmar**.
7. Confirmación definida: cada observación indica una prueba o comprobación concreta con actor, recurso y resultado esperado cuando corresponda.
8. Estado de pruebas veraz: cada prueba figura como "ejecutada" (con comando y resultado real) o "pendiente". No hay resultados inventados.
9. Contexto verificado en SHA: toda afirmación sobre controles ausentes o presentes se apoya en contexto obtenido en el SHA de cabeza (y en el de base para eliminaciones o comparaciones), no en el contenido actual de una rama ni en el checkout local.
10. Sección de comprobaciones: se listan los controles y cambios examinados, incluso si no hubo observaciones, y las pruebas ejecutadas o pendientes.
11. Caso sin observaciones: si no hay hallazgos, el informe lo declara expresamente y describe qué controles y cambios se comprobaron, junto con el contexto que no pudo revisarse.
12. Cierre de alcance: el informe termina con la nota de que la revisión se limita al criterio de autorización y no constituye una aprobación del PR.
13. Sin publicación: no se publicaron comentarios, revisiones ni aprobaciones en el PR.
14. Sin hallazgos fuera de criterio: no aparecen observaciones sobre otros aspectos de seguridad, pruebas generales o compatibilidad.
15. Sin secretos ni datos reales: el informe no contiene credenciales, tokens ni datos de producción.

Criterios de limitación (aceptables solo si se declaran en el informe):

- MCP no disponible, PR o diff no accesible, página faltante, SHA que no pueden fijarse o relacionarse con el diff, o contexto necesario no obtenible.
- En estos casos, las observaciones se limitan a riesgos sustentados en el diff, marcados como "riesgo por confirmar", y se especifica qué falta confirmar.

Verificación final antes de cerrar:

- Relee el informe y confirma que cada sección del formato está presente.
- Confirma que cada enlace, SHA y número de línea proviene de la consulta MCP realizada, no de suposiciones.
- Confirma que no se modificaron archivos del repositorio distintos del informe.
