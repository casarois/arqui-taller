---
name: generar-seccion
description: Genera secciones longitudinales o transversales desde el modelo 3D de cualquier proyecto, con corte, tres planos de profundidad, rellenos que ocultan, terreno, agua, vegetación y personas.
---
Lee `C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller\.claude\skills\_COMUN.md`.

**Entrada**: modelo 3D (capas `3D_`), línea de corte (curva en `PLANTA_08_LINEAS_SECCION` o dos puntos), dirección de vista, profundidad máxima, escala, y si va sola o dentro de una lámina de conjunto.
**Scripts**: `capas.main`, `seccion.main`, `rellenos.main`, `version.main`, `captura.main`, `exportar.main`.

## Pasos
1. Confirma: nombre (A-A', B-B'…), prefijo (`SECCION_LONG`, `SECCION_TRANS` u otro), vista, límites de los planos 01/02/03 en metros desde el corte, escala, `reducir` (True si va en lámina de conjunto).
2. `capas.main("fachada", prefijo, reducir)` y `capas.main("seccion_paisaje", prefijo, reducir)`.
3. `seccion.main(linea, vista, prefijo, planos=(d1, d2), profundidad_max=...)`:
   lo cortado → `_04_SILUETA` + terreno; lo visto → `_01/_02/_03` según distancia.
4. `rellenos.main(prefijo=prefijo)`: rellenos blancos bajo las aristas de cada plano para ocultar lo de detrás.
5. Terreno: relleno `_07_TERRENO` + `_07_TERRENO_LINEA`. Agua: `_08_AGUA` + `_08_AGUA_LAMINA` si existe.
6. Vegetación y personas: proyecta los bloques del modelo; si no hay, pregunta (librería, dejarlo para postpro o nada).
7. Cota ±0.00, alturas principales y pie "SECCIÓN A-A' · E 1:___".
8. Dibuja la línea en planta (`PLANTA_08_LINEAS_SECCION`) con sus letras.
9. `captura.main(zona)` → revisar → `exportar.main`.

## Revisar
- Jerarquía: silueta > terreno > primer plano > segundo > fondo > detalle.
- Todo lo cortado tiene relleno; los rellenos tapan bien lo de detrás.
- Prefijo correcto en todas las capas; ninguna capa con nombre antiguo.
