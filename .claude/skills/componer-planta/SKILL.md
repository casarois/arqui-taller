---
name: componer-planta
description: "Compone plantas de cualquier proyecto (edificio o urbana) desde el modelo 3D o geometría 2D: corte, capas, rellenos, recintos, cotas y layout."
---
Lee `C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller\.claude\skills\_COMUN.md`.

**Entrada**: modelo 3D o dibujo 2D, tipo (edificio / urbana), nivel y altura de corte, escala, formato.
**Scripts**: `capas.main`, `planta.main`, `rellenos.main`, `recintos.main`, `cotas.main`, `captura.main`, `exportar.main`.

## Pasos
1. `capas.main("lamina")` + `capas.main("planta_edificio")` o `("planta_urbana")`.
2. 3D → `planta.main(nivel, altura=1.20)` (`nivel` = cota Z del suelo en metros; el 2D sale en z=0): lo cortado a `PLANTA_10_MUROS_CORTE`, lo visto a `_13_VISTA`. Pilares a `_11_PILARES` y lo superior a `_14_PROYECCIONES`, a mano (el script no los separa).
   2D → lista qué capa propones para cada grupo y espera OK (o usa **auditar-capas**).
3. `rellenos.main("PLANTA_10_MUROS_CORTE", "PLANTA_10_MUROS_CORTE_RELLENO")`.
4. `recintos.main(capa_recintos)` (capa del encargo; si no viene, `DUDA`) → nombre y m² por recinto; confirma los nombres.
5. `cotas.main(niveles=3)`: total, ejes y huecos por fuera; interiores solo si se piden.
6. Norte, escala gráfica, pie → `captura.main(zona)` → `exportar.main`.

## Revisar
- Corte frente a vista: nada cortado en capa de vista.
- Textos y cotas sin solapes; m² que sumen la superficie total.
