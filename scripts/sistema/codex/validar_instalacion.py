"""Comprueba identidad de fuentes y archivos de entrada, sin abrir Rhino."""
import argparse
import json
import os
import tomllib
from pathlib import Path

from preparar_instalacion import CENTRAL, DESTINO, PYTHON


def validate(root, links=True):
    root = Path(root)
    with (root / ".codex" / "config.toml").open("rb") as stream:
        config = tomllib.load(stream)
    assert str(CENTRAL) in config["sandbox_workspace_write"]["writable_roots"]
    assert config["features"]["hooks"] is True
    assert PYTHON.is_file(), "Falta Python configurado para hooks"
    profiles = []
    with (Path.home() / ".codex" / "models_cache.codex_work_desktop.json").open(encoding="utf-8") as stream:
        models = {item["slug"] for item in json.load(stream)["models"]}
    for source in (CENTRAL / ".claude" / "agents").glob("*.md"):
        with (root / ".codex" / "agents" / (source.stem + ".toml")).open("rb") as stream:
            profile = tomllib.load(stream)
        assert profile["name"] == source.stem
        assert profile["model"] in models, profile["model"]
        assert str(source) in profile["developer_instructions"], "Instruccion duplicada o fuente perdida"
        profiles.append(profile["name"])
    hooks = json.loads((root / ".codex" / "hooks.json").read_text(encoding="utf-8"))
    for event in ("PreToolUse", "SessionStart", "SubagentStart", "SubagentStop"):
        command = hooks["hooks"][event][0]["hooks"][0]["command"]
        assert str(CENTRAL / "scripts" / "sistema" / "codex" / "hook_equipo.py") in command
        assert str(DESTINO) in command
    shared = []
    if links:
        for name in ("scripts", "normas", "proyectos"):
            assert (root / name).is_junction(), f"{name} no es un enlace Junction"
            assert os.path.samefile(root / name, CENTRAL / name), f"{name} es otra fuente"
            shared.append(name)
        assert os.path.samefile(root / "registro", CENTRAL / "registro" / "codex")
        for source in (CENTRAL / ".claude" / "skills").glob("*/SKILL.md"):
            entry = root / ".agents" / "skills" / source.parent.name
            assert entry.is_junction(), str(entry)
            assert os.path.samefile(entry / "SKILL.md", source), "Skill copiada"
            shared.append(source.parent.name)
        specific = root / ".agents" / "skills" / "control-uso" / "SKILL.md"
        assert os.path.samefile(specific, CENTRAL / "adaptadores" / "codex" / "skills" / "control-uso" / "SKILL.md")
        assert os.path.samefile(root / "scripts" / "puente" / "rhino.ps1", CENTRAL / "scripts" / "puente" / "rhino.ps1")
    return {"taller": str(root), "perfiles": len(profiles), "fuentes_compartidas": shared,
            "configuracion": "valida", "rhino": "sin ejecutar", "hooks": "requieren confianza del usuario en Codex"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--taller", default=str(DESTINO))
    parser.add_argument("--paquete", action="store_true", help="Validar archivos antes de instalar enlaces")
    args = parser.parse_args()
    print(json.dumps(validate(args.taller, links=not args.paquete), ensure_ascii=False, indent=2))
