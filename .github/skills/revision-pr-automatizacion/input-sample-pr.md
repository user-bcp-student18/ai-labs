Antes de iniciar la revisión local de autorización del PR, verifica que se cumplan los criterios de entrada. Si alguno falla, detente y solicita la información faltante; no continúes con supuestos.

Criterios obligatorios:

1. URL del PR: debe estar presente y apuntar a un pull request accesible. Si falta, solicítala.
2. Herramientas MCP: deben estar disponibles para consultar el PR, sus referencias base y cabeza, y el diff completo. Si no lo están, informa la limitación y no presentes la revisión como completa.
3. Alcance: la revisión se limita exclusivamente a la autorización de acceso y modificación de recursos (comprobaciones de permisos, propiedad y aislamiento entre tenants, incluidas eliminaciones o cambios en controles existentes). No incluyas otros aspectos de seguridad, pruebas generales ni compatibilidad.

Criterios opcionales:
4. Ruta del informe local: si se indica, úsala; si no, usa `revision-pr-<numero>.md` en la raíz del workspace. Si el archivo ya existe, no lo sobrescribas: solicita otra ruta o usa un nombre disponible.

Condiciones previas al análisis:
5. Obtén la URL, el repositorio, el número, y los nombres y SHA completos de las referencias base y cabeza mediante MCP. No uses el checkout local como sustituto del PR ni del diff.
6. Recupera el diff completo de esos SHA, incluidas todas las páginas. Confirma que base y cabeza son consistentes; si el PR cambia durante la consulta, vuelve a obtener las referencias y el diff. No mezcles versiones.
7. Si el diff no puede fijarse por SHA, falta alguna página o no puede relacionarse con sus SHA, detente y repórtalo en el informe.

Restricciones:

- No publiques comentarios, revisiones ni aprobaciones en el PR.
- No inventes evidencia ni resultados de pruebas. Registra una prueba como ejecutada solo si se ejecutó, con comando y resultado; en caso contrario, márcala como pendiente.
- No supongas que una comprobación falta sin verificar el contexto en el SHA de cabeza (y en el de base cuando aplique a una eliminación o comparación).

Confirma los criterios de entrada indicando, para cada uno, si se cumple, y luego procede con la revisión y el informe con el formato definido en el skill.
