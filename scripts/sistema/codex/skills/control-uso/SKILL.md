---
name: control-uso
description: Mide un encargo del taller en Codex con tokens de la sesion y sus trabajadores y muestras del uso del plan. Usar al empezar y terminar tareas con herramientas o al consultar su consumo; no usar en Claude.
---

# Control de uso de Codex

Solo lo ejecuta el orquestador. Los trabajadores no abren ni cierran contadores.
El script unico vive en el taller central:
`C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller\scripts\sistema\codex\uso_encargo.py`.

Python disponible en este ordenador:
`C:\Program Files\QGIS 3.44.14\apps\Python312\python.exe`.
Ejecutar desde PowerShell, con `-X utf8` antes de la ruta del script.

## Inicio y fin

Antes del trabajo con herramientas, descubre y llama a la herramienta de la app
`get_usage_limits` (nombre actual `mcp__codex_app__get_usage_limits`) si esta
disponible. Prefiere `rateLimitsByLimitId.codex` a `rateLimits`. De cada ventana
lee `usedPercent`, `windowDurationMins` y `resetsAt`. Nunca leer archivos de
autenticacion para consultar el uso.

Ejecutar:

```powershell
& 'C:\Program Files\QGIS 3.44.14\apps\Python312\python.exe' -X utf8 'C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller\scripts\sistema\codex\uso_encargo.py' --fase inicio --encargo 'Nombre breve'
```

Al terminar el encargo, incluso si queda interrumpido o pendiente:

```powershell
& 'C:\Program Files\QGIS 3.44.14\apps\Python312\python.exe' -X utf8 'C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller\scripts\sistema\codex\uso_encargo.py' --fase fin
```

El identificador se toma de `CODEX_THREAD_ID` o `CODEX_SESSION_ID`; si no estan
disponibles, pasar `--sesion <id exacto>` y, si hace falta, `--transcripcion <jsonl>`.
No seleccionar el chat mas reciente ni una transcripcion de Claude. Un seguimiento
del mismo encargo conserva el inicio: repetir inicio no lo sustituye. Repetir fin
devuelve el mismo informe sin duplicar el CSV.

Cuando hayas consultado la app, anade al comando de inicio o fin los valores
obtenidos en esa consulta: `--uso-5h <usedPercent> --reinicio-5h <resetsAt>` para
la ventana de 300 minutos y `--uso-semanal <usedPercent> --reinicio-semanal
<resetsAt>` para la de 10080 minutos. Repite la consulta antes de cerrar. Omite
la pareja si su valor es nulo o falta. Si la herramienta no esta disponible, el
script usa la ultima muestra del rollout e informa de su fecha y procedencia;
no la presentes como una consulta en vivo. No inventes ni reutilices valores de
un encargo anterior. Ventanas con otras duraciones quedan en la muestra local.

Para consultar sin iniciar/cerrar: `--fase estado`. El registro se escribe en
`arqui-taller\registro\codex\`: estado por sesion, informe JSON por encargo y CSV.
No tocar `UNI\CLAUDE\registro-uso\`.

## Presentar resultados

Mostrar tabla breve por modelo: entrada, cache leida (incluida en entrada), salida
y total. El razonamiento ya forma parte de la salida observada: no volver a sumarlo.
Informar los tokens como **observados en el registro local**, hasta la lectura;
la respuesta posterior que cierra el encargo no entra.

Del campo `plan`, mostrar porcentaje antes/despues, fecha de la muestra y diferencia
solo si `delta` tiene valor. Es una diferencia observada de toda la cuenta, no el
consumo exacto del encargo. Una ventana de 300 minutos corresponde a 5 h y 10080
minutos a una semana. Mostrar ventanas distintas con su duracion real.

Si faltan muestras, ha cambiado el reinicio o no hay datos nuevos, decirlo; no
presentar cero como consumo confirmado. `coste_api_usd` y `estimado_plan_pct` son
nulos deliberadamente: no usar los precios ni el factor de conversion de Claude.
El limite semanal habitual es 10%; el script avisa si la diferencia observada lo
supera, pero no garantiza imponer un presupuesto exacto.

Si el formato cambia o no se identifica la sesion, reportar el fallo sin inventar
cifras. El contador no es necesario para acceder a Rhino y no lee autenticacion.
