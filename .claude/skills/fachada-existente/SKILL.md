---
name: fachada-existente
description: Dibuja alzados o fachadas detalladas (huecos, carpinterías, cornisas, cubiertas, texturas) de edificios existentes o de proyecto, desde modelo 3D, foto rectificada o croquis acotado, con jerarquía por profundidad.
---
Lee `C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller\.claude\skills\_COMUN.md`.

**Entrada**: fuente (3D / foto rectificada + una cota conocida / croquis acotado), fachada y orientación, escala, nivel de detalle (esquema / medio / detalle).
**Scripts**: `capas.main`, `alzado.main`, `foto_escala.main`, `repetir_huecos.main`, `rellenos.main`, `captura.main`, `exportar.main`.

## Pasos
1. Prefijo `ALZADO_<NOMBRE>` (o el de la sección si va dentro de ella) y `capas.main("fachada", prefijo, reducir)`.
2. Según fuente:
   - 3D → `alzado.main(vista, prefijo, planos)` reparte aristas en 01/02/03.
   - Foto → `foto_escala.main(imagen, p1, p2, distancia)` y se calca encima. Si la foto no está rectificada, avisa de la deformación.
   - Croquis → pide las cotas que falten antes de dibujar.
3. Silueta (`_04_SILUETA`) y planos 01/02/03.
4. Huecos: dibuja un tipo por clase y repítelo con `repetir_huecos.main`. Detalles en este orden: huecos, arcos, contraventanas, impostas/cornisas, cubiertas, planta baja, textura de muro, balcones.
5. Textura de muro solo en nivel "detalle" y siempre la línea más fina.
6. `rellenos.main(prefijo=prefijo)` para ocultar planos traseros.
7. `captura.main(zona)` → revisar → `exportar.main`.

## Revisar
- Huecos alineados por plantas y ejes; simetrías.
- La textura no compite con los huecos.
- Siluetas cerradas.
