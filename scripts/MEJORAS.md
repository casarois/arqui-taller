# Mejoras pendientes de los scripts del taller

Solo la escribe el **orquestador** (los subagentes proponen mejoras en el apartado `MEJORA:` de su informe).
La prioridad la decide **el usuario**: el orquestador le enseña la lista ordenada y lanza **un solo encargo por lotes** al `programador-rhino` con las que elija.

Cuándo se revisa con el usuario:
- cuando una fila llega a **2 apariciones** (misma falta o misma corrección en dos encargos: regla 7 de `CLAUDE.md`);
- o cuando haya **5 o más** filas `abierta`, o hayan pasado **2 semanas** desde la última revisión.

Tipos: `FALTA SCRIPT` · `SCRIPT FALLA` · `código improvisado` (un subagente escribió su propio código: ver `registro\codigo_improvisado.log`) · `corrección repetida` (el usuario corrige lo mismo) · `idea`.
Estado: `abierta` → `en lote <fecha>` → `hecha <commit>` / `descartada (motivo)`.
Si una mejora ya está en la lista, no se añade otra fila: se suma 1 a **Veces** y se añade la evidencia nueva.

Última revisión con el usuario: — (ninguna aún)

| # | Fecha | Encargo | Tipo | Script | Qué | Evidencia | Veces | Estado |
|---|---|---|---|---|---|---|---|---|
| 1 | 2026-11-08 | v7 parco-gpii (comparación equipo / Opus solo) | idea | `nucleo\captura.py` | Solo hace vistas en planta: falta perspectiva (u otra vista con nombre) para el `modelador-3d` | `captura.main` captura una zona x0,y0,x1,y1 en planta; el modelador no tiene cómo verificar el volumen | 1 | abierta |
| 2 | 2026-11-08 | v7 parco-gpii | idea | `dibujo\recortar_base.py` | Lista los hatch afectados pero no los recorta | Contrato en `INDEX.md` ("los hatch afectados se listan (no se recortan)"); en la v7 el relleno del lago queda bajo la huella nueva | 1 | abierta |
| 3 | 2026-11-08 | v7 parco-gpii | idea (normas) | `revision\holgura.py` | Separación mínima proyecto/contexto de 2 mm sin confirmar por el usuario | `normas\grafismo.json` → `composicion.holgura_proyecto_contexto_mm: 2.0` | 1 | abierta |
| 4 | 2026-11-08 | v7 parco-gpii | idea (normas) | — | Escala 1:1000 del plano de situación sin confirmar (la lámina no lleva texto de escala) | `proyectos\parco-gpii\PROYECTO.md` (apartado escala) | 1 | abierta |
| 5 | 2026-11-08 | — (INDEX.md) | FALTA SCRIPT | `dibujo\planta.py` | Parcial: no separa pilares ni dibuja `_14_PROYECCIONES`; omite bloques y SubD | `INDEX.md` estado "parcial" | 1 | abierta |
| 6 | 2026-11-08 | — (INDEX.md) | FALTA SCRIPT | `revision\auditar.py` | Informe de capas vs normas; con aplicar renombra/corrige | `INDEX.md` "pendiente"; lo usa la skill `auditar-capas` | 1 | abierta |
| 7 | 2026-11-08 | — (INDEX.md) | FALTA SCRIPT | `dibujo\seccion.py` | Corte vertical → planos 01/02/03 + silueta | `INDEX.md` "pendiente"; skill `generar-seccion` | 1 | abierta |
| 8 | 2026-11-08 | — (INDEX.md) | FALTA SCRIPT | `dibujo\alzado.py` | Make2D frontal → planos 01/02/03 | `INDEX.md` "pendiente"; skill `fachada-existente` | 1 | abierta |
| 9 | 2026-11-08 | — (INDEX.md) | FALTA SCRIPT | `dibujo\axo.py` | Vista paralela + Make2D → capas AXON | `INDEX.md` "pendiente"; skill `axonometria` | 1 | abierta |
| 10 | 2026-11-08 | — (INDEX.md) | FALTA SCRIPT | `dibujo\explotar.py` | Copia y separa en Z por niveles | `INDEX.md` "pendiente" | 1 | abierta |
| 11 | 2026-11-08 | — (INDEX.md) | FALTA SCRIPT | `dibujo\sombras.py` | Sombras proyectadas en planta/axo | `INDEX.md` "pendiente" | 1 | abierta |
| 12 | 2026-11-08 | — (INDEX.md) | FALTA SCRIPT | `dibujo\recintos.py` | Nombre + m² por recinto cerrado | `INDEX.md` "pendiente"; skill `componer-planta` | 1 | abierta |
| 13 | 2026-11-08 | — (INDEX.md) | FALTA SCRIPT | `dibujo\cotas.py` | Cotas exteriores en niveles | `INDEX.md` "pendiente" | 1 | abierta |
| 14 | 2026-11-08 | — (INDEX.md) | FALTA SCRIPT | `dibujo\foto_escala.py` | Foto de fondo escalada a medida real | `INDEX.md` "pendiente"; skill `fachada-existente` | 1 | abierta |
| 15 | 2026-11-08 | — (INDEX.md) | FALTA SCRIPT | `dibujo\repetir_huecos.py` | Matriz de un hueco tipo | `INDEX.md` "pendiente" | 1 | abierta |
| 16 | 2026-11-08 | — (INDEX.md) | FALTA SCRIPT | `lamina\comparativo.py` | Layouts estado actual / propuesta | `INDEX.md` "pendiente"; skill `modificar-con-boceto` | 1 | abierta |
| 17 | 2026-11-08 | — (INDEX.md) | FALTA SCRIPT | `lamina\lamina.py` | Layout del formato con papel, marco, retícula, cabecera, pie | `INDEX.md` "pendiente"; skill `maquetar-lamina` | 1 | abierta |
| 18 | 2026-11-08 | — (INDEX.md) | FALTA SCRIPT | `lamina\detalle.py` | Detail con escala exacta en una caja de la retícula | `INDEX.md` "pendiente" | 1 | abierta |
| 19 | 2026-11-08 | — (INDEX.md) | FALTA SCRIPT | `postpro\capas_png.py` | PNG transparente por grupo de capas, mismo encuadre | `INDEX.md` "pendiente"; skill `postpro-collage` | 1 | abierta |
| 20 | 2026-11-08 | — (INDEX.md) | FALTA SCRIPT | `postpro\ps_montar.jsx` | Monta PSD con los PNG en grupos fijos | `INDEX.md` "pendiente" | 1 | abierta |
| 21 | 2026-11-08 | — (INDEX.md) | FALTA SCRIPT | `entrega\entrega.py` | Última versión → comprobar → renombrar → imprimir/ | `INDEX.md` "pendiente"; skill `preparar-entrega` | 1 | abierta |
| 22 | 2026-11-08 | pruebas de regresión | idea (pruebas) | `nucleo\exportar.py` | La rama con layouts (PDF de varias páginas, preview de la vista activa) y `dwg=True` no se prueban | Ningún archivo de `pruebas\archivos\` tiene layouts; hace falta uno con 1-2 layouts | 1 | abierta |
| 23 | 2026-11-08 | pruebas de regresión | SCRIPT FALLA (potencial) | `nucleo\exportar.py` | No añade las subcarpetas de `scripts\` a `sys.path` (bloque `_S` de la plantilla): solo funciona por el puente | `import util` (l. 17) e `import captura` (l. 131) sin el bloque de rutas (l. 11-17) | 1 | abierta |
| 24 | 2026-11-08 | pruebas de regresión | idea (pruebas) | `dibujo\recortar_base.py` | Faltan casos: `lado="fuera"`, contorno rectangular (x0,y0,x1,y1) y `fragmento_min` | Solo hay prueba de `lado="dentro"` con curva | 1 | abierta |
| 25 | 2026-11-08 | pruebas de regresión | idea | `puente\rhino.ps1` | `-Codigo`/`-Archivo` devuelve todo lo impreso como un único texto con saltos de línea, no una línea por elemento | `probar.ps1` no encontraba `RESULTADO` hasta partir por saltos de línea | 1 | abierta |
| 26 | 2026-11-08 | bucle de mejora | idea | `sistema\hook_codigo.ps1` | Sin verificar que la entrada del hook trae `agent_type` cuando escribe un subagente (si no, anota "(principal o sin tipo)") | Probado solo con entradas simuladas; mirar la primera línea real del log | 1 | abierta |
| 27 | 2026-11-08 | pruebas de regresión | idea | `pruebas\probar.ps1` | `salida\` crece ~45 MB por ejecución y no se vacía sola | Informe del programador; LEEME dice vaciar a mano | 1 | abierta |
