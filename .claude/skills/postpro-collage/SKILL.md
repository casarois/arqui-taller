---
name: postpro-collage
description: Postproduce planos, secciones, axonometrías o vistas en Photoshop o GIMP (opcional ComfyUI/Krita) para láminas y collages de cualquier proyecto, sin alterar la geometría.
---
Lee `C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller\.claude\skills\_COMUN.md`.

**Entrada**: dibujo base de Rhino, tipo (plano / sección / axonometría / collage / vista), referencias de tono (carpeta del usuario), formato y resolución.
**Scripts**: `capas_png.main` (Rhino) y `ps_montar.jsx` (Photoshop: `C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller\scripts\postpro\ps_montar.jsx`). Los dos están pendientes. Photoshop 2024 no tiene COM ni MCP: los JSX se lanzan con `Photoshop.exe "script.jsx"`.

## Pasos
1. `capas_png.main(grupos, dpi=300)`: un PNG transparente por grupo (líneas, rellenos, agua, vegetación, fondo), mismo encuadre.
2. PSD del formato final con grupos fijos:
   `00_FONDO / 01_RELLENOS / 02_TEXTURAS / 03_SOMBRAS / 04_LINEAS (multiplicar) / 05_VEGETACION_PERSONAS / 06_AMBIENTE / 07_TEXTOS`.
3. Texturas, personas y vegetación: solo las que aporte el usuario o de su carpeta de referencias. Anota su procedencia en un `.txt` junto al PSD.
4. Tono: compara con las referencias del usuario (paleta, contraste, saturación) y ajústalo con capas de ajuste, no destructivas.
5. IA opcional (ComfyUI/Krita): la imagen de líneas como control (lineart/depth), denoise bajo; nunca sustituye las líneas.
6. Guarda PSD editable + JPG preview + PNG/PDF final con los nombres de normas.

## Revisar
- Las líneas siguen nítidas y encima.
- Resolución final = formato × 300 ppp.
- Coherencia con las referencias; nada que tape el proyecto.
