"""Genera la configuracion local de Codex; no copia contenido comun del taller."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

CENTRAL = Path(__file__).resolve().parents[3]
DESTINO = Path(r"C:\Users\2402l\Documents\UNI\CODEX\arqui-taller")
PYTHON = Path(r"C:\Program Files\QGIS 3.44.14\apps\Python312\python.exe")


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def prepare(output):
    output = Path(output)
    source = CENTRAL / ".claude" / "agents"
    for path in sorted(source.glob("*.md")):
        content = path.read_text(encoding="utf-8-sig")
        front = content.split("---", 2)[1]
        name = re.search(r"^name:\s*(.+)$", front, re.M)[1].strip()
        description = re.search(r"^description:\s*(.+)$", front, re.M)[1].strip()
        old_effort = re.search(r"^effort:\s*(.+)$", front, re.M)
        effort = old_effort[1].strip() if old_effort else "medium"
        model = "gpt-6-luna" if name == "auxiliar-tecnico" else "gpt-6.1-sol"
        if name == "auxiliar-tecnico":
            effort = "high"
        instructions = (
            f"Eres el perfil {name} del taller de arquitectura en Codex.\n"
            f"Lee {CENTRAL / 'adaptadores' / 'codex' / 'ADAPTADOR.md'}.\n"
            f"Lee el cuerpo del perfil compartido {path}, omitiendo su frontmatter YAML.\n"
            "Sigue ese cuerpo y las reglas comunes que referencia. No copies ni mantengas otra version de ellas.\n"
            "El modelo y esfuerzo validos son los de este perfil TOML. Los nombres de modelos de Claude no se aplican.\n"
            "No delegues, no preguntes al usuario ni ejecutes control-uso; devuelve las dudas al orquestador.\n"
            "Usa las skills y scripts centrales. Nunca desarrolles un script paralelo para Codex.\n"
        )
        if name == "critico":
            instructions += "Solo lee y revisa: no ejecutes ediciones, guardados, exportaciones ni cambios en Rhino.\n"
        body = "\n".join(f"{key} = {json.dumps(value, ensure_ascii=False)}" for key, value in (
            ("name", name), ("description", description), ("model", model),
            ("model_reasoning_effort", effort), ("developer_instructions", instructions))) + "\n"
        write(output / ".codex" / "agents" / (name + ".toml"), body)
    config = f'''# Configuracion solo de esta entrada; no cambia la configuracion global ni Claude.
# El modelo del orquestador lo elige el usuario en Codex.
project_doc_max_bytes = 65536

[features]
hooks = true

[agents]
enabled = true
max_concurrent_threads_per_session = 3

[sandbox_workspace_write]
writable_roots = [{json.dumps(str(CENTRAL))}]
'''
    write(output / ".codex" / "config.toml", config)
    command = f'"{PYTHON}" -X utf8 "{CENTRAL / "scripts" / "sistema" / "codex" / "hook_equipo.py"}" --taller "{DESTINO}"'
    hooks = {"description": "Equipo del taller compartido: controles Codex y registro propio.", "hooks": {}}
    for event, matcher in (("PreToolUse", "^(Agent|spawn_agent)$"), ("SessionStart", "startup|resume|clear|compact|fork"),
                           ("SubagentStart", "*"), ("SubagentStop", "*")):
        handler = {"type": "command", "command": command, "timeout": 15,
                   "statusMessage": "Comprobando equipo del taller"}
        hooks["hooks"][event] = [{"matcher": matcher, "hooks": [handler]}]
    write(output / ".codex" / "hooks.json", json.dumps(hooks, ensure_ascii=False, indent=2) + "\n")
    instructions = f'''# Taller de arquitectura en Codex

Responde en espanol. Esta es una entrada al taller comun, no otra implementacion.
Central: `{CENTRAL}`.

Antes de trabajar, lee `{CENTRAL / 'adaptadores' / 'codex' / 'ADAPTADOR.md'}` y
`{CENTRAL / 'CLAUDE.md'}`. El primero sustituye solo los elementos de plataforma
(modelos, herramientas, hooks y consumo). Conserva el flujo y criterio de la
fuente comun. Para tareas de arquitectura lee el PROYECTO.md y normas del proyecto.

Las diez skills se descubren en `.agents/skills` mediante enlaces a las originales.
La skill `control-uso` es la adaptacion Codex, tambien almacenada en el central.
Los perfiles se definen en `.codex/agents`; usa el perfil nativo por su nombre,
sin sustituir modelos al lanzar. El orquestador conserva el modelo elegido por
el usuario. El critico es obligatorio antes de entregar una pieza producida.

`scripts`, `normas`, `proyectos` y `registro` son enlaces a las fuentes centrales.
Toda correccion de codigo, norma, skill o instruccion de especialidad va a su
fuente central. Nunca crees una copia "Codex" de un script de Rhino, una skill
de arquitectura, una norma ni un proyecto. Si falta un enlace, reparalo; no copies
el contenido. Conserva el esquema actual de versiones y los originales.

El puente sigue siendo `scripts/puente/rhino.ps1` y `abrir_rhino.ps1` del central.
No sustituirlo por otro MCP ni por otra implementacion. Escoger siempre PID/doc
y una copia antes de modificar, segun las reglas compartidas.

El control de uso se abre/cierra por encargo con la skill Codex. Los trabajadores
no lo ejecutan. No uses el contador, tarifas ni calibracion de Claude. Nunca leas
claves o tokens. No cambies la configuracion global del usuario para este taller.

Los hooks necesitan revision/confianza en la app. Si no estan activos, informa
de ello; no des por hecho que las restricciones ya se estan comprobando.
'''
    write(output / "AGENTS.md", instructions)
    readme = f'''# Abrir el taller en Codex

1. Abre esta carpeta como proyecto en Codex: `{DESTINO}`.
2. Revisa/confia el proyecto si la app lo solicita. Abre Ajustes > Hooks (o `/hooks`
   en CLI) y revisa los hooks nuevos antes de usarlos. No se ha modificado tu
   configuracion global ni se ha aceptado esa confianza automaticamente.
3. Empieza un chat nuevo aqui. Puedes pedir: "Comprueba el taller y lista los
   Rhinos disponibles, sin modificar ningun documento".

Los enlaces apuntan a `{CENTRAL}`. Cambiar un script o una skill enlazada cambia
la unica fuente que usa tambien Claude. No uses esta carpeta como plantilla para
copiarla a otros proyectos; no hay sincronizacion, hay archivos compartidos.

| Especialidad | Modelo Codex |
|---|---|
| Auxiliar tecnico | GPT-6 Luna, esfuerzo high |
| Las otras ocho especialidades | GPT-6.1 Sol, esfuerzo medium/high segun perfil |
| Orquestador | El que elijas en la app |

Modelos configurados con los identificadores disponibles en este equipo al instalar.
Las instrucciones de los perfiles se leen de la fuente central; los TOML solo
adaptan su carga y seleccion de modelo a Codex.

Registro propio: `registro/` -> `central/registro/codex/`. El contador entrega
tokens observados y diferencias del plan de toda la cuenta si hay muestras validas.
No convierte esas cifras a coste o porcentaje atribuible al encargo sin calibracion.

Documentacion de mantenimiento: `{CENTRAL / 'adaptadores' / 'codex' / 'ADAPTADOR.md'}`.
Instalador: `{CENTRAL / 'scripts' / 'sistema' / 'codex' / 'instalar.ps1'}`.

La validacion inicial de archivos y pruebas sinteticas no acredita todavia una
sesion real de produccion en Rhino desde este nuevo proyecto. El puente y los
dibujos existentes se han conservado.
'''
    write(output / "LEEME.md", readme)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", required=True)
    print(prepare(parser.parse_args().salida))
