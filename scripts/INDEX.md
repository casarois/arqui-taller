# Índice de scripts
Raíz: `C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller\scripts\`. Rhino 8.5 / Python 3 salvo que se indique.
Por el puente, todas las subcarpetas ya están en `sys.path`: `import util`, `import capas`… funcionan directamente.
Scripts nuevos: copiar `nucleo\_plantilla.py` a la subcarpeta indicada aquí, cumplir el contrato de esta tabla, probar en copia, marcar "listo".
Todos devuelven **una línea** de resumen. Los que modifican objetos existentes: `aplicar=False` por defecto.
En las carpetas de proyectos no va ningún script: todos viven aquí.

| Carpeta | Para qué |
|---|---|
| `puente\` | Conexión Claude ↔ Rhino abierto |
| `nucleo\` | Base común de todos los scripts de Rhino (normas, capas, versiones, exportar, captura, plantilla) |
| `dibujo\` | Generar dibujo 2D: plantas, secciones, alzados, axonometrías, rellenos, recortes, cotas… |
| `revision\` | Comprobar archivos frente a normas (capas, holgura con el contexto) |
| `lamina\` | Maquetación de láminas y layouts (aún vacía: todo pendiente) |
| `postpro\` | Paso a Photoshop/GIMP (aún vacía: todo pendiente) |
| `entrega\` | Reunir y renombrar la entrega (aún vacía: todo pendiente) |
| `sistema\` | Funcionamiento del equipo (hooks de subagentes y de código improvisado) y alias del control de uso |
| `pruebas\` | Pruebas de regresión de los scripts "listos": `probar.ps1`, casos (`casos\`), valores esperados (`esperado.json`), archivos fijos (`archivos\`, solo lectura) y resultados (`salida\`). Cómo añadir una: `LEEME.md` |

| Carpeta | Script | Qué hace | Parámetros | Dónde | Estado |
|---|---|---|---|---|---|
| puente | puente_rhino.py | Puente local 127.0.0.1:4250-4259 (uno por Rhino): ejecuta en el Rhino abierto el Python que envía `rhino.ps1`. Solo arranca; se cierra con Rhino | — | Rhino | listo |
| puente | puente_parar.py | Para el puente de ese Rhino | — | Rhino | listo |
| puente | puente_iniciar.py | Alias de `puente_rhino.py` (compatibilidad) | — | Rhino | listo |
| puente | rhino.ps1 | Cliente del puente: `-Codigo '...'` o `-Archivo x.py`; `-Lista`; elegir Rhino con `-Doc` o `-Id`; `-Cerrar` cierra ese Rhino de forma normal (`-Guardar` guarda antes; sin él descarta los cambios no guardados) y espera a que termine | `Codigo, Archivo, Lista, Doc, Id, Puerto, Cerrar, Guardar` | PowerShell | listo |
| puente | abrir_rhino.ps1 | Abre un Rhino nuevo con un .3dm y el puente arrancado; devuelve PID y puerto | `Archivo, Espera=180` | PowerShell | listo |
| nucleo | util.py | Normas (+proyecto), plantillas, equivalencias, clasificar, versiones | — | cualquiera | listo |
| nucleo | capas.py | Crea/actualiza capas de una plantilla | `plantilla, prefijo=None, reducir=False, solo=None` | Rhino | listo |
| nucleo | version.py | Guarda en vN+1 y sigue en la copia | — | Rhino | listo |
| nucleo | exportar.py | Copia 3dm (`editable=False` no la crea: útil si el archivo de trabajo ya está en la carpeta), DWG, PDF por layout y preview PNG. **Sin layouts** y con capa de papel (`LAMINA_00_PAPEL`): PDF del rectángulo del papel a escala 1:1 desde espacio modelo (layout temporal que se borra al acabar) y preview = `captura.main()` del papel | `tema, formato="A2", version="v1", carpeta=None, pdf=True, dwg=True, preview=True, editable=True` | Rhino | listo |
| nucleo | captura.py | PNG de una zona del modelo con grosores y colores de impresión (PrintDisplay) y encaje exacto (escala por píxel conocida, sin rejilla ni ejes). `zona=None` → rectángulo de la capa de papel (`LAMINA_00_PAPEL`), o extensión del dibujo si no hay. `ancho_px` manda sobre `ppmm` (para igualar el tamaño de un PNG anterior). Devuelve ruta, píxeles y zona real. `lado_a_lado(pngs, salida, titulos=None)` monta PNG de la misma zona uno junto a otro (antes / después). `salida` = carpeta (nombre automático, no sobrescribe) o ruta `.png` exacta; tras `main()`, `captura.ULTIMA` = ruta del PNG; `capturar(...)` devuelve un dict | `zona=None` (x0,y0,x1,y1 en unidades del doc), `salida=None` (carpeta del doc), `ppmm=10, ancho_px=None, impresion=True` | Rhino | listo |
| nucleo | _plantilla.py | Plantilla para scripts nuevos | — | Rhino | listo |
| revision | auditar.py | Informe de capas vs normas; con aplicar renombra/corrige | `aplicar=False` | Rhino | pendiente |
| revision | holgura.py | Distancia mínima en planta entre las curvas de las capas del proyecto y las del contexto (por prefijo de capa, incluidas las equivalencias antiguas), dentro de `zona`. Compara con `minimo` (si es None, `composicion.holgura_proyecto_contexto_mm` de normas) y da la capa y el punto del peor caso. Solo curvas de capas visibles (ignora hatch), proyectadas a z=0 y recortadas a `zona` | `proyecto="PLANTA_06_ARQUITECTURAS", contexto=("PLANTA_01_EDIFICIOS",), zona=None, minimo=None` | Rhino | listo |
| dibujo | rellenos.py | Hatch sólido (color por capa) de curvas cerradas, justo detrás de las líneas; curvas interiores = huecos; abiertas se ignoran y se cuentan. Dos usos: una capa → otra (`origen`, `destino`; si falta destino se deriva solo si existe en normas: `_ARISTAS`→`_RELLENOS`, `_CONTORNO`→`_RELLENO`, `+_RELLENO`), o todos los planos de una sección/alzado (`prefijo=`: cada `{P}_0N_*_ARISTAS` → `_RELLENOS`, reordena el orden de dibujo 01>02>03) | `origen=None, destino=None, prefijo=None` (o `origen` o `prefijo`) | Rhino | listo |
| dibujo | planta.py | Corte horizontal de las capas `3D_` visibles a z = (`nivel`+`altura`) en metros (se convierte a unidades del doc) → 2D en z=0: corte a `PLANTA_10_MUROS_CORTE`, visto por debajo (Make2D) a `PLANTA_13_VISTA`. No separa pilares ni dibuja `_14_PROYECCIONES`; omite bloques y SubD | `nivel, altura=1.20` | Rhino | parcial |
| dibujo | seccion.py | Corte vertical → 2D en planos 01/02/03 + silueta | `linea, vista, prefijo, planos=(d1,d2), profundidad_max=None` | Rhino | pendiente |
| dibujo | alzado.py | Make2D frontal → planos 01/02/03 | `vista, prefijo, planos=(d1,d2)` | Rhino | pendiente |
| dibujo | axo.py | Vista paralela + Make2D → capas AXON | `tipo, angulo, corte=None` | Rhino | pendiente |
| dibujo | explotar.py | Copia y separa en Z por niveles | `niveles, separacion` | Rhino | pendiente |
| dibujo | sombras.py | Sombras proyectadas en planta/axo | `sol` (vector o orientación+hora) | Rhino | pendiente |
| dibujo | recortar_base.py | Recorta curvas contra un contorno cerrado (id de curva o rectángulo x0,y0,x1,y1). `lado="fuera"`: borra lo exterior (recortar la base a un ámbito); `lado="dentro"`: borra lo interior (líneas de agua, curvas de nivel u orillas que quedan bajo una huella nueva). `margen` = las líneas terminan esa distancia antes del borde (en unidades del doc). `capas` = nombres o prefijos afectados (None = todas las visibles salvo la del contorno). Lista los fragmentos sueltos más cortos que `fragmento_min` y, con aplicar, los borra. Los hatch afectados se listan (no se recortan) | `ambito, margen=0, lado="fuera", capas=None, fragmento_min=0, aplicar=False` | Rhino | listo |
| dibujo | recintos.py | Nombre + m² por recinto cerrado (la capa la da el encargo) | `capa_recintos` (obligatorio) | Rhino | pendiente |
| dibujo | cotas.py | Cotas exteriores en niveles | `niveles=3, lados="todos"` | Rhino | pendiente |
| dibujo | foto_escala.py | Foto de fondo escalada a medida real | `imagen, p1, p2, distancia` | Rhino | pendiente |
| dibujo | repetir_huecos.py | Matriz de un hueco tipo | `hueco, filas, columnas, paso_x, paso_y` | Rhino | pendiente |
| lamina | comparativo.py | Layouts estado actual / propuesta | `modo="dos_layouts"` | Rhino | pendiente |
| lamina | lamina.py | Layout del formato con papel, marco, retícula, cabecera, pie | `formato, orientacion, titulo, datos` | Rhino | pendiente |
| lamina | detalle.py | Detail con escala exacta en una caja de la retícula | `vista, escala, caja` | Rhino | pendiente |
| postpro | capas_png.py | PNG transparente por grupo de capas, mismo encuadre | `grupos, dpi=300, carpeta=None` | Rhino | pendiente |
| postpro | ps_montar.jsx | Monta PSD con los PNG en grupos fijos | `carpeta_png, formato` | Photoshop | pendiente |
| entrega | entrega.py | Última versión → comprobar → renombrar → imprimir/ | `carpeta, laminas, datos, simular=True` | Python | pendiente |
| sistema | uso_encargo.ps1 | **Alias**: reenvía a la skill general `UNI\CLAUDE\.claude\skills\control-uso\uso_encargo.ps1`, que es donde vive el script. Control de uso por encargo: % de 5 h y semanal (toda la cuenta, lo lee el orquestador con `get_usage`) antes/después/gastado, y tokens reales y coste equivalente API por modelo de esta sesión + subagentes (de la transcripción local, no les afectan otras sesiones). Además estima el % semanal y de 5 h del encargo a partir del coste (calibrado con tus encargos: ≈ 300 $/semana y ≈ 43 $/5 h; `-Fase calibrar` lo recalcula) y anota el gasto de todas las sesiones del ordenador en ese tiempo. Imprime el cuadro y lo anota en `UNI\CLAUDE\registro-uso\uso_encargos.csv`; avisa si se reinicia una ventana o se supera el límite semanal | `Fase inicio\|fin, Encargo, Uso5h, UsoSemanal, Reinicio5h, ReinicioSemanal, Transcripcion="" (auto), LimiteSemanal=10, ValorSemanal=300, Valor5h=43` | PowerShell | listo |
| pruebas | probar.ps1 | Pruebas de regresión: por cada archivo de `archivos\` hace una copia nueva en `salida\<aaaammdd_hhmmss>\`, la abre con `abrir_rhino.ps1`, ejecuta los casos de `esperado.json` (`casos\_comun.py` + `casos\caso_*.py`, que imprimen `RESULTADO {json}`), compara con tolerancias y cierra el Rhino sin guardar pase lo que pase. Solo lectura del mismo archivo: un Rhino compartido; `modifica=true`: copia y Rhino propios. Una línea por prueba (OK / FALLO obtenido vs esperado) y `PRUEBAS: n OK, m FALLO`; código 0 todo OK, 1 algún fallo, 2 ninguna prueba. Cubre captura, holgura, recortar_base y exportar (sin layouts). Ejecutar tras cambiar cualquier script probado | `Solo=""` (nombre o script, admite comodines), `Esperado=""` (otro json) | PowerShell | listo |
| sistema | hook_equipo.ps1 | Hook: bloquea `model` al lanzar subagentes y subagentes genéricos; registra en `registro\equipo.log`. Solo actúa dentro de arqui-taller | — | PowerShell | listo |
| sistema | hook_codigo.ps1 | Hook PreToolUse `Write\|Edit` (en la configuración de usuario): en sesiones de arqui-taller, cada `.py` escrito o editado **fuera de `scripts\`** (código improvisado) se anota en `registro\codigo_improvisado.log` (fecha · agente · herramienta · ruta · líneas · primera línea). Nunca bloquea. El orquestador lo pasa a `MEJORAS.md` (regla 8) | JSON por stdin | PowerShell | listo |

## Entrada Codex (fuentes comunes, configuración independiente)

Codex se abre en `C:\Users\2402l\Documents\UNI\CODEX\arqui-taller`.
Sus enlaces apuntan a este taller: los scripts Rhino anteriores no se duplican.
Adaptación y mantenimiento: `adaptadores/codex/ADAPTADOR.md`.
Los scripts de integración siguientes se ejecutan **fuera de Rhino** con Python
3.11+ (disponible en QGIS Python312) o PowerShell 7; sus informes son JSON, no el
resumen de una línea de los scripts de dibujo.

| Carpeta | Script | Qué hace | Parámetros | Estado |
|---|---|---|---|---|
| sistema/codex | uso_encargo.py | Diferencia de tokens de la sesión exacta y sus descendientes identificados; muestras del plan de toda la cuenta; registro separado en registro/codex | `--fase inicio\|fin\|estado`, `--encargo`, `--sesion`, `--transcripcion`, `--sesiones`, `--registro`, `--limite-semanal=10` | listo; pruebas sintéticas y lectura real |
| sistema/codex | hook_equipo.py | Comprueba lanzamientos de perfiles y registra eventos Codex sin guardar prompts; no cambia el hook de Claude | JSON por stdin, `--taller`, `--registro` | listo; pendiente de confianza/activación en nuevo proyecto |
| sistema/codex | preparar_instalacion.py | Genera TOML de agentes, config, hooks y documentos de entrada; cada perfil referencia sus instrucciones centrales | `--salida` | listo |
| sistema/codex | instalar.ps1 | Instala entrada Codex y enlaces Junction; rechaza reemplazar archivos distintos y no borra ni mueve originales | `-Paquete`, `-Destino` (solo destino elegido) | listo |
| sistema/codex | validar_instalacion.py | Comprueba perfiles, modelos, hooks y que skills/normas/scripts/proyectos sean los mismos archivos | `--taller` | listo |
| sistema/codex | test_integracion.py | Pruebas de tokens, aislamiento, reinicios y controles sin abrir Rhino ni llamar modelos | — | listo |
