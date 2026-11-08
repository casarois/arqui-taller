# Pruebas de regresión de los scripts

Comprueban en un comando que los scripts "listos" siguen dando lo mismo tras un arreglo o una mejora.

**Ejecutar** (PowerShell fuera del sandbox; ~1 min, abre y cierra sus propios Rhinos):
`& "C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller\scripts\pruebas\probar.ps1"` — todas.
`-Solo holgura` → solo las de ese script o con ese nombre (admite comodines: `-Solo "holgura_*"`).
Salida: una línea por prueba (`OK` / `FALLO` con obtenido y esperado) y `PRUEBAS: n OK, m FALLO`; código 0 si todo OK, 1 si algo falla.

**Cómo funciona**: copia el archivo de `archivos\` (solo lectura, no tocar) a `salida\<aaaammdd_hhmmss>\<grupo>\`, lo abre con `abrir_rhino.ps1`, envía a Rhino `casos\_comun.py` + el caso, lee la línea `RESULTADO {json}` y la compara con `esperado.json`. Cierra el Rhino sin guardar pase lo que pase. Las pruebas de solo lectura del mismo archivo comparten Rhino; las de `"modifica": true` tienen copia y Rhino propios.

**Añadir una prueba**:
1. Si el script no tiene caso, crea `casos\caso_<script>.py`: llama al script con `PARAMS` (de esperado.json), deja lo que genere en `SALIDA` y termina con `resultado(clave=valor, ...)`. Utilidades en `_comun.py`: `campo`, `numero`, `png_tam`, `tinta`, `pdf_paginas`, `archivos`, `en_planta`, `unidades`.
2. Añade una entrada en `esperado.json`: `nombre, script, archivo, caso, modifica, parametros, esperado`. Cada clave de `esperado` admite `{"valor", "tol"}`, `{"igual"}`, `{"min"}` y/o `{"max"}`.
3. Ejecuta `probar.ps1 -Solo <nombre>`. Los valores esperados se miden a mano o vienen de un resultado conocido: **nunca se ajustan para que pase**.

`salida\` y `archivos\` están fuera de git; `salida\` crece ~45 MB por ejecución (copias 3dm): vacíala a mano cuando quieras.
