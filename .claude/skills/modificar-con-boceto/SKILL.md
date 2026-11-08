---
name: modificar-con-boceto
description: Aplica a un proyecto existente (3dm, dwg, dxf) de cualquier tipo los cambios dibujados en un boceto o foto (rojo = nuevo, amarillo = derribo) o pedidos de palabra (p. ej. "este edificio, de circular a cuadrado"), y genera el comparativo estado actual / propuesta.
---
Lee `C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller\.claude\skills\_COMUN.md`.

**Entrada**: archivo del proyecto + boceto (mejor dibujado sobre una impresión del plano, con cotas en cada cambio) o descripción del cambio.
**Scripts**: `version.main`, `captura.main` / `captura.lado_a_lado`, `capas.main("propuesta")`, `recortar_base.main`, `rellenos.main`, `holgura.main`, `comparativo.main`.

## Pasos
1. Lee el boceto o el encargo: cada cambio con su referencia (muro, eje, hueco existente) y su cota.
2. Devuelve una lista numerada de cambios. Lo ambiguo, marcado **DUDA**. No toques nada hasta el OK.
3. `version.main()` (o la copia que indique el encargo). Antes de tocar nada:
   - `captura.main(zona, salida)` de la zona del cambio → `antes_<zona>.png`.
   - Mide lo que vas a sustituir: centro, ejes, huella, medidas principales, paso de gradas o peldaños, capas y grosores, y el retranqueo con que las líneas del contexto mueren contra él.
4. **Criterio de diseño**: las medidas salen de lo existente (mismo centro y ejes, proporciones y ritmos traducidos). Una medida del encargo que no venga medida es orientativa: si al medir choca (deja huecos, pisa el contexto), ajusta lo mínimo y dilo en **Revisar**.
5. Dónde se dibuja:
   - **Con comparativo** (boceto estado actual / propuesta): `capas.main("propuesta")`; nuevo en `PROPUESTA_01_NUEVO`, derribo en `PROPUESTA_02_DERRIBO`. El original no se borra.
   - **Modificación directa de una lámina**: en la copia de versión, se sustituye en **las capas del archivo** y con el mismo grosor que lo que se quita. Si el archivo usa nombres antiguos, no se crean capas de normas (pasarlas es un encargo aparte de `auditar-capas`).
6. Contexto bajo la huella:
   - Si la huella nueva no cubre la anterior, repara lo que esta tapaba (agua, curvas, orillas).
   - Lo que queda debajo de la nueva: `recortar_base.main(contorno_nuevo, margen=<retranqueo medido>, lado="dentro", capas=...)`, primero sin aplicar, revisa la lista y luego con `aplicar=True`.
   - Rellenos con `rellenos.main`, en el mismo orden de dibujo que tenían.
7. `holgura.main(zona=...)` con el contexto construido; si no llega al mínimo de normas, corrige o explica.
8. Salida en la carpeta de la versión:
   - `captura.main(zona)` → `despues_<zona>.png` y `captura.lado_a_lado([antes, despues])` → `comparacion_<zona>.png`.
   - Lámina completa: `captura.main(ancho_px=<ancho del PNG de la versión anterior>)`.
   - `NOTAS.md`: criterios de diseño, medidas finales y qué se ha tocado del contexto.
9. Si se pide: `comparativo.main()` → layouts "estado actual" y "propuesta".

## Revisar
- Cada cambio de la lista está hecho y nada más; lo no pedido sigue igual (capas, grosores, orden de dibujo).
- Lo nuevo pesa como lo que sustituye: mismo grosor y jerarquía que en la versión anterior.
- Sin restos bajo la huella anterior ni trozos sueltos; agua y curvas mueren igual que antes contra el borde.
- Holgura con el contexto ≥ `composicion.holgura_proyecto_contexto_mm`.
- Las cotas del boceto se respetan; si chocan con el plano, se pregunta.
