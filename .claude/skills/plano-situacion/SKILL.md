---
name: plano-situacion
description: "Crea un plano de situación o implantación para cualquier proyecto desde una base urbana (3dm, dwg, dxf): recorta el ámbito, clasifica en capas de normas, rellena edificios, agua y vegetación y destaca el proyecto."
---
Lee `C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller\.claude\skills\_COMUN.md`.

**Entrada**: base cartográfica, ámbito (curva/rectángulo, o centro + escala + formato), escala, qué elementos mostrar, qué es "proyecto".
**Scripts**: `version.main`, `recortar_base.main`, `auditar.main`, `capas.main`, `rellenos.main`, `holgura.main`, `captura.main`, `exportar.main`.
Para cambiar algo de un plano de situación ya hecho (un edificio, un palco), usa **modificar-con-boceto**.

## Pasos
1. Ámbito = (formato − márgenes) × escala. Propón el rectángulo y confirma.
2. Nunca trabajes sobre la base original: `version.main()` o copia en la carpeta del dibujo.
3. `recortar_base.main(ambito, margen, lado="fuera")`: corta las curvas en el borde y descarta lo exterior (sin `aplicar` primero; revisa la lista).
4. Clasifica capas de la base con la skill **auditar-capas** (las bases traen capas en cualquier idioma). Plantillas `lamina` + `planta_urbana`.
5. `rellenos.main(origen, destino)` para: edificios, singulares, agua (gradación 1-3 si hay profundidad), base blanca del proyecto. Lista las curvas abiertas que no se pudieron rellenar.
6. Curvas de nivel: pregunta la equidistancia de las maestras.
7. Proyecto en `PLANTA_06_ARQUITECTURAS` sobre `_BASE` blanca; contexto en grises.
8. Norte, escala gráfica, título → `holgura.main()` → `captura.main()` del papel → `exportar.main` (si la lámina está en espacio modelo, saca el PDF del papel).

## Revisar
- Contraste: el proyecto se lee primero.
- El proyecto no pisa el contexto construido: holgura ≥ `composicion.holgura_proyecto_contexto_mm`.
- Rellenos sin solapes ni huecos; agua bajo las líneas de orilla.
- Nada fuera del ámbito; texto de calles legible a la escala.
