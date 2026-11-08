"""Adaptador de eventos Codex. No altera el hook ni los registros de Claude."""
from __future__ import annotations

import argparse
import json
import os
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

CENTRAL = Path(__file__).resolve().parents[3]


def inside(path, root):
    path = os.path.normcase(str(Path(path).resolve()))
    root = os.path.normcase(str(Path(root).resolve()))
    return path == root or path.startswith(root + os.sep)


def profiles(root):
    result = {}
    for path in (Path(root) / ".codex" / "agents").glob("*.toml"):
        with path.open("rb") as stream:
            item = tomllib.load(stream)
        result[item["name"]] = item
    return result


def decide(event, agents):
    if event.get("hook_event_name") != "PreToolUse":
        return None
    if event.get("tool_name") not in ("Agent", "spawn_agent"):
        return None
    args = event.get("tool_input") or {}
    role = args.get("agent_type") or args.get("subagent_type") or args.get("task_name")
    if role not in agents and role != "explorer":
        return "Usa un perfil del taller o explorer para buscar archivos. No se admite un agente generico."
    if args.get("model"):
        return "El modelo se fija en .codex/agents/<perfil>.toml; no lo cambies al lanzar el agente."
    if args.get("effort") or args.get("reasoning_effort"):
        return "El esfuerzo se fija en el perfil; los cambios solicitados se configuran alli."
    return None


def handle(event, root, log_dir):
    if not inside(event.get("cwd") or ".", root):
        return {}
    agents = profiles(root)
    name = event.get("hook_event_name")
    args = event.get("tool_input") or {}
    role = event.get("agent_type") or args.get("agent_type") or args.get("subagent_type") or args.get("task_name")
    denial = decide(event, agents)
    entry = {"at": datetime.now(timezone.utc).isoformat(), "event": name,
             "session_id": event.get("session_id"), "turn_id": event.get("turn_id"),
             "agent_id": event.get("agent_id"), "role": role, "model": event.get("model"),
             "decision": "deny" if denial else "observe"}
    folder = Path(log_dir)
    folder.mkdir(parents=True, exist_ok=True)
    # Una linea pequena por evento; sin prompts, codigo ni contenido de documentos.
    with (folder / "equipo.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(entry, ensure_ascii=False) + "\n")
    if denial:
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                        "permissionDecisionReason": denial}}
    if name == "SessionStart":
        return {"hookSpecificOutput": {"hookEventName": name, "additionalContext":
                "Taller Codex: lee AGENTS.md. Skills, normas, scripts y proyectos son enlaces al taller central. "
                "Usa control-uso de Codex al inicio y al fin del encargo; no ejecutes el contador de Claude."}}
    if name == "SubagentStart":
        text = "Lee el perfil compartido y equipo_comun.md indicados por tus instrucciones. No delegues ni ejecutes control-uso."
        if role in agents and event.get("model") and event["model"] != agents[role].get("model"):
            text += " El modelo observado no coincide con el perfil: informa al orquestador antes de producir."
        return {"hookSpecificOutput": {"hookEventName": name, "additionalContext": text}}
    return {}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--taller", required=True)
    parser.add_argument("--registro", default=str(CENTRAL / "registro" / "codex"))
    args = parser.parse_args()
    try:
        event = json.load(sys.stdin)
        result = handle(event, args.taller, args.registro)
        print(json.dumps(result, ensure_ascii=False))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        # No presentar un fallo del control como un permiso concedido.
        print(f"No se pudo comprobar el equipo del taller: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
