---
name: maquetar-lamina
description: "Monta láminas de presentación (A1, A2, A3) de cualquier proyecto en un layout de Rhino o en Inkscape: marco, cabecera, dibujos a escala, columna de información, textos y pie."
---
Lee `C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller\.claude\skills\_COMUN.md`.

**Entrada**: formato y orientación, piezas (dibujos con su escala, imágenes, textos), título, datos del cajetín.
**Scripts**: `capas.main("lamina")`, `lamina.main`, `detalle.main`, `exportar.main`.

## Pasos
1. Confirma formato, orientación y lista de piezas con su escala.
2. `lamina.main(formato, orientacion, titulo, datos)`: layout + papel, marco, retícula (normas → `maquetacion`) en capa de guías no imprimible, cabecera y pie.
3. Por pieza: `detalle.main(vista, escala, caja)` con escala exacta y marco de dibujo. Imágenes: insertar o pasar a Inkscape si la lámina es mayoritariamente imagen.
4. Jerarquía de textos de normas → `textos`; pie de cada dibujo "NOMBRE · E 1:___".
5. Columna de información: leyenda, esquemas pequeños (con `reducir=True`), notas.
6. Revisa solapes y márgenes con una captura del layout → `exportar.main`.

## Revisar
- Todo alineado a la retícula; márgenes iguales.
- Escalas reales en los detalles (no "a ojo").
- Un solo dibujo protagonista.
