---
name: axonometria
description: Genera axonometrías (isométrica, militar o caballera) desde el modelo 3D de cualquier proyecto como dibujo de líneas con jerarquía, sombras y rellenos; opción seccionada o explotada.
---
Lee `C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller\.claude\skills\_COMUN.md`.

**Entrada**: modelo con capas `3D_` (si no, pasar antes por **auditar-capas** con plantilla `modelo_3d`), tipo y ángulo, alcance, seccionada (plano) o explotada (separación), escala.
**Scripts**: `capas.main`, `axo.main`, `explotar.main`, `sombras.main`, `rellenos.main`, `captura.main`, `exportar.main`.

## Pasos
1. Confirma tipo (isométrica 30/30, militar 45/45 o 30/60), qué entra y si es seccionada o explotada.
2. `capas.main("axon")`.
3. Explotada → `explotar.main(niveles, separacion)` en una copia.
4. `axo.main(tipo, angulo, corte=None)`: vista paralela + Make2D; las capas `3D_` van a sus `AXON_`: suelo → 01/02, contexto → 05, singulares → 06, vegetación → 07, proyecto → 09/10.
5. `sombras.main(sol)` (pregunta orientación y hora o un vector) → `AXON_04_*`.
6. `rellenos.main` para cubiertas del proyecto, verde y caras de corte.
7. Personas, etiquetas y título con fondo blanco detrás (`AXON_08`, `_11`, `_12`).
8. `captura.main(zona)` del dibujo 2D → revisar → `exportar.main`.

## Revisar
- El proyecto (negro/azul) destaca sobre el contexto gris.
- Contorno del proyecto (`AXON_10`) es la línea más gruesa.
- Sin aristas duplicadas ni ocultas visibles (salvo que se pidan).
