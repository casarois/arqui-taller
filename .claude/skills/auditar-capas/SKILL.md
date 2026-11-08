---
name: auditar-capas
description: Revisa un archivo Rhino de cualquier proyecto y lo ajusta a las normas (renombrar capas, grosores, colores, tipos de línea). Úsala antes de trabajar sobre un archivo antiguo, heredado o descargado.
---
Lee `C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller\.claude\skills\_COMUN.md`.

**Entrada**: archivo .3dm abierto. Plantillas que aplican (si no se dicen, dedúcelas por los prefijos y confirma).
**Scripts**: `auditar.main(aplicar=False)`, `capas.main(plantilla)`, `version.main()`.

## Pasos
1. Unidades y nº de objetos. Si hay más de 20.000, trabaja solo con datos por capa.
2. `auditar.main(aplicar=False)` → informe en contadores: ok / renombrar / corregir grosor-color / sin equivalente / capa por defecto con objetos / vacías.
3. Muestra solo lo que cambia. Para cada "sin equivalente" propone destino:
   - si es propio de este proyecto → añadir a `normas_proyecto.json` (equivalencia o capa nueva);
   - si serviría en cualquier proyecto → proponer añadirlo a `grafismo.json`.
4. OK del usuario → `version.main()` → `auditar.main(aplicar=True)` → `capas.main(...)` para las que falten.
5. Repite el informe: debe dar 0 renombrar, 0 corregir, 0 sin equivalente.

## Revisar
- No se borra nada: capas vacías y antiguas solo se listan.
- Al fusionar dos capas en una, avisa (se pierde la distinción).
- Subcapas: se comparan por nombre final; no aplanar sin pedirlo.
