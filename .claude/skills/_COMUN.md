# Reglas comunes a todas las skills
Taller (normas, scripts, puente): `C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller`

- **Conexión con Rhino**: puente propio (`arqui-taller\scripts\puente\rhino.ps1`, `abrir_rhino.ps1`), no MCP. Ver "Ejecutar en Rhino" en `C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller\CLAUDE.md`.
- **Normas**: `arqui-taller\normas\grafismo.json` + `normas_proyecto.json` del proyecto si existe (util.normas lo suma solo). Nada gráfico se inventa.
- **Scripts**: mira `arqui-taller\scripts\INDEX.md` (carpetas: `puente`, `nucleo`, `dibujo`, `revision`, `sistema`; `lamina`, `postpro` y `entrega` aún sin scripts). Si el que pide la skill está "pendiente" o no existe:
  - Subagente que no es `programador-rhino`: para y devuelve `FALTA SCRIPT: <nombre> — <para qué>` (no lo escribas tú).
  - `programador-rhino` (o el orquestador en los casos de la regla 6 de `CLAUDE.md`): parte de `nucleo\_plantilla.py`, cumple el contrato del índice, prueba en copia y marca "listo"; si cambian parámetros, actualiza el índice y la skill. Nada específico de un proyecto dentro de los scripts.
- **Versiones**: antes de modificar, `version.main()` (guarda en vN+1 y sigue en la copia).
- **Capas de un archivo existente**: si usa nombres antiguos (los de `equivalencias_antiguas`), se dibuja en sus capas, con el grosor que ya tienen. Pasarlas a nombres de normas es un encargo aparte (**auditar-capas**); nunca se mezclan capas antiguas y nuevas en el mismo archivo. Para saber qué grosor de normas corresponde a una capa antigua, sigue la equivalencia.
- **Confirmación**: lista de cambios → OK del usuario → ejecutar.
- **Verificación**: una captura al final con `captura.main` (no escribas código de captura propio); checklist "Revisar" de la skill.
- **Cerrar Rhino**: `rhino.ps1 -Id <pid> -Cerrar` (`-Guardar` si hay que guardar). Nunca a la fuerza.
- **Respuesta**: hecho / pendiente / revisar.
