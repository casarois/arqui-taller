# Entrada de Codex al taller compartido

Central: `C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller`.
Entrada de Codex: `C:\Users\2402l\Documents\UNI\CODEX\arqui-taller`.

## Fuentes que se mantienen una sola vez

- Flujo del orquestador, criterios de diseno y tecnica Rhino: `CLAUDE.md` del central.
- Instrucciones de cada especialidad: cuerpo (despues del frontmatter) de `.claude/agents/<perfil>.md`.
- Procedimientos: `.claude/skills/<skill>/SKILL.md` y `.claude/skills/_COMUN.md` del central.
- Reglas de los trabajadores: `equipo_comun.md` del central.
- Normas: `normas/grafismo.json` + `proyectos/<nombre>/normas_proyecto.json`.
- Contexto: `proyectos/<nombre>/PROYECTO.md`.
- Codigo: `scripts/`, con contrato en `scripts/INDEX.md`.

El nombre historico `.claude` no implica una segunda implementacion. Los enlaces
de Codex apuntan a esos mismos archivos. No copiar, sincronizar ni reimplementar
una skill, norma o script para cada cliente. Editar la fuente central una vez.
Una correccion de un script Rhino debe beneficiar a ambos clientes.

## Adaptaciones de plataforma

En Codex, leer las fuentes anteriores aplicando estas sustituciones concretas:

1. Los nombres Opus/Sonnet/Haiku y las cabeceras YAML `model`, `effort`, `tools`,
   `skills`, `maxTurns`, `color` pertenecen a Claude. El modelo y el esfuerzo de
   Codex se fijan en `.codex/agents/<perfil>.toml` de la entrada Codex. El cuerpo
   de la especialidad se lee siempre del central; no se copia a los TOML.
2. Invocar el perfil nativo por su nombre exacto. No pasar un modelo alternativo
   en el lanzamiento. Si el cliente no expone perfiles personalizados, informar
   de la limitacion y configurar ese cliente antes de producir; un `task_name`
   por si solo no garantiza cargar un perfil ni elegir su modelo.
3. `Explore` se corresponde con `explorer` para busquedas, sin producir piezas.
   Usar las herramientas de colaboracion disponibles para continuar el mismo
   trabajador. Los trabajadores no delegan ni preguntan al usuario.
4. Usar la skill `control-uso` propia de Codex enlazada a
   `adaptadores/codex/skills/control-uso`. No ejecutar el contador de Claude, no
   usar `mcp__ccd_session_mgmt__get_usage`, ni sus precios/calibracion. El uso de
   los trabajadores lo suma el contador del orquestador cuando hay filiacion
   explicita en el registro. Un seguimiento del mismo encargo no abre otro.
5. El hook de Codex se configura en `.codex/hooks.json`. El de Claude y su
   configuracion de usuario quedan intactos. El hook comprueba lanzamientos
   soportados y registra eventos; no sustituye los permisos del sistema ni
   concede aprobaciones. Los hooks necesitan revision y confianza en Codex.
6. `Read`, `Glob`, `Grep`, `PowerShell`, `Skill`, `SendMessage` y nombres semejantes
   de las fuentes describen acciones: usar la herramienta equivalente de Codex.
   El critico solo lee, incluso si hereda herramientas con capacidad de escribir.
7. Las rutas relativas `arqui-taller/...` de las fuentes se resuelven contra el
   central. La entrada de Codex enlaza `scripts`, `normas` y `proyectos` al central.
   Nunca crear otra biblioteca Rhino bajo la entrada Codex ni en un proyecto.
8. La regla de ejecutar PowerShell del puente fuera del sandbox describe la
   necesidad observada en este equipo. Usar la via de permisos disponible; no
   desactivar el sandbox global. El contador funciona con lectura de rollouts.

Todo lo demas conserva el comportamiento del taller: confirmaciones del flujo,
versiones antes de modificar, una copia y un Rhino por trabajador, capas antiguas
respetadas, capturas comparables y revision critica antes de entregar.

## Alcance inicial y mantenimiento

La instalacion no cambia los scripts existentes, los dibujos ni los perfiles de
Claude. Se han entrecomillado las descripciones YAML de cuatro skills para que
sean validas en ambos clientes, conservando su texto y procedimientos. Los
originales estan respaldados en `UNI/CLAUDE/migracion-codex/respaldo-skills/`.
El indice de scripts incorpora los nuevos auxiliares. Estos viven en `scripts/sistema/codex/` del
central. El registro Codex vive en `registro/codex/`; no mezcla filas con Claude.

El contador prefiere porcentajes consultados por la herramienta `get_usage_limits`
de la app; se los pasa el orquestador. Sin ella, usa muestras locales con su fecha
y procedencia. Nunca consulta autenticacion por su cuenta.

El contador admite encargos concurrentes en chats distintos (estado por id de
sesion). Cuenta diferencias de contadores acumulados y evita sumar dos veces
cache, razonamiento o muestras repetidas. Las muestras del plan pertenecen a
toda la cuenta y pueden llegar con retraso. Si cambia su reinicio, no publica una
diferencia valida. No convierte tokens en porcentaje ni dolares sin datos propios.
El formato de los rollouts no es una interfaz estable: revisar ante una actualizacion.

Si se anade una nueva skill al central, volver a ejecutar `instalar.ps1`: agrega
su enlace sin sustituir los existentes. Si se modifica un SKILL.md ya enlazado,
no hace falta reinstalar. Las altas/cambios de perfiles se preparan con
`preparar_instalacion.py`; se comparan antes de actualizar la configuracion local.

Fuentes oficiales consultadas el 2026-11-08:
- https://learn.chatgpt.com/docs/agent-configuration/subagents
- https://learn.chatgpt.com/docs/build-skills
- https://learn.chatgpt.com/docs/hooks
- https://learn.chatgpt.com/docs/agent-configuration/agents-md
