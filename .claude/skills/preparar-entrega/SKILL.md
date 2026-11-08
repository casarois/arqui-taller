---
name: preparar-entrega
description: "Prepara la entrega de cualquier proyecto: elige la última versión de cada lámina, comprueba formato y resolución, renombra según el patrón de entrega y lo reúne en una carpeta imprimir sin tocar los originales."
---
Lee `C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller\.claude\skills\_COMUN.md`.

**Entrada**: carpeta del proyecto, láminas (o "las últimas versiones"), proyecto, autor, formato, patrón de entrega (normas → `nombres.entrega`).
**Scripts**: `entrega.main` (Python normal, fuera de Rhino).

## Pasos
1. `entrega.main(carpeta, laminas, datos, simular=True)` → tabla lámina → nombre final, con avisos.
2. Muestra la tabla y espera OK.
3. Comprueba: tamaño de página = formato, nº de páginas, peso (aviso si > 50 MB), resolución de imágenes.
4. `entrega.main(..., simular=False)`: copia a `imprimir/`, renombra y genera JPG de cada PDF.
5. Resumen: archivos creados y avisos.

## Revisar
- Nada sobrescrito: si un nombre existe, añade `_2`.
- Todas las láminas son la última versión (vN más alta).
- Nombres sin tildes ni espacios raros.
