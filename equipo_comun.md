# Reglas comunes del equipo (las lee cada subagente al empezar)

Eres un subagente del equipo de arquitectura. Recibes un ENCARGO del orquestador y lo ejecutas tú: no delegas en nadie.

1. **Encargo**: haz exactamente lo pedido. Si falta un dato esencial (escala, archivo, capas, criterio), no lo inventes: termina y devuélvelo como `DUDA: …`. No puedes preguntar al usuario.
2. **Rhino**: trabaja solo con el puente (sección "Ejecutar en Rhino" de `C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller\CLAUDE.md`). PowerShell del puente siempre fuera del sandbox.
   - Usa tu propio Rhino: el `-Doc`/`-Id` que indique el encargo, o abre una copia con `abrir_rhino.ps1`. Nunca el archivo original.
   - `version.main()` antes de modificar. No borres ni sobrescribas.
   - En archivos de más de 20.000 objetos, consulta por capa.
   - Al acabar, ciérralo con `rhino.ps1 -Id <pid> -Cerrar` (`-Guardar` si toca).
3. **Normas**: todo valor gráfico sale de `arqui-taller\normas\grafismo.json` + `normas_proyecto.json`. Si falta uno: `DUDA`.
   - En un archivo con capas de nombre antiguo, trabaja en sus capas y con sus grosores (ver `_COMUN.md`). Si el encargo pide crear capas nuevas en él, es una contradicción: `DUDA`.
   - Si una medida del encargo choca con lo que mides en el archivo (deja huecos, pisa el contexto), ajusta lo mínimo y explícalo en **Revisar**; si el cambio es grande, `DUDA`.
4. **Scripts**: usa los de `arqui-taller\scripts\INDEX.md`. No los escribas ni los modifiques tú (salvo que seas `programador-rhino`):
   - Si el que necesitas está "pendiente" o no existe: para y devuelve `FALTA SCRIPT: <nombre> — <para qué>`.
   - Si falla: para y devuelve `SCRIPT FALLA: <nombre> — <llamada exacta> — <error completo>`, para que el orquestador lo arregle sin repetir tu trabajo.
5. **Captura**: al terminar, guarda una captura PNG con `captura.main` en la carpeta de salida (no escribas tu propio código de captura). Si modificas un dibujo existente, además: captura **antes** de tocar nada, `captura.lado_a_lado` antes/después de la misma zona y un `NOTAS.md` con tus criterios (skill `modificar-con-boceto`).
6. **Respuesta final** (breve, sin repetir el encargo):
   - **Hecho**: qué has hecho.
   - **Pendiente**: qué falta y por qué.
   - **Revisar**: lo que debe mirar el orquestador.
   - **Archivos**: rutas de lo creado (3dm, captura, exportaciones).
   - **DUDAS / FALTA SCRIPT / SCRIPT FALLA** si los hay.
   - **MEJORA:** una línea por cada cosa que habría ido mejor con una herramienta del taller, aunque hayas acabado el encargo: `tipo · script · qué · evidencia`. Tipos: `FALTA SCRIPT`, `SCRIPT FALLA`, `código improvisado` (has tenido que escribir código tuyo, aunque sea una línea, para medir, capturar o comprobar algo: di qué hacía), `idea`. Si no hay ninguna, `MEJORA: ninguna`. No escribas en `scripts\MEJORAS.md`: la pasa el orquestador.
