"""Uso de Codex por encargo. Python 3.11+, biblioteca estandar; nunca lee claves.

El formato JSONL de Codex no es una API estable. Se mide por diferencia de
contadores acumulados; cache y razonamiento son subconjuntos, no sumandos.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

FIELDS = ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens", "total_tokens")
CENTRAL = Path(__file__).resolve().parents[3]


def now():
    return datetime.now(timezone.utc).isoformat()


def events(path):
    # Windows: el escritor de Codex mantiene abierto el rollout. Python abre con
    # comparticion de lectura/escritura; no usar File.Open exclusivo de .NET.
    with Path(path).open(encoding="utf-8-sig") as stream:
        for line in stream:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                # Un ultimo registro sin salto de linea puede seguir escribiendose.
                if line.endswith("\n"):
                    raise ValueError(f"JSONL no reconocido en {Path(path).name}")


def metadata(path):
    for index, event in enumerate(events(path)):
        if event.get("type") == "session_meta":
            return event["payload"]
        if index >= 4:
            break
    return {}


def parent_id(meta):
    source = meta.get("source")
    if not isinstance(source, dict):
        return None
    spawn = source.get("subagent", {}).get("spawn", {})
    return spawn.get("parent_thread_id") or spawn.get("parent_session_id")


def session_paths(root, session_id, explicit=None):
    index = {}
    warnings = []
    for path in Path(root).rglob("*.jsonl"):
        try:
            meta = metadata(path)
        except (OSError, ValueError):
            continue
        if meta.get("id"):
            if meta["id"] in index:
                warnings.append(f"Sesion duplicada {meta['id']}; se cuenta una sola copia")
            else:
                index[meta["id"]] = (path, meta)
    if explicit:
        meta = metadata(explicit)
        if meta.get("id") != session_id:
            raise ValueError("La transcripcion no pertenece a la sesion indicada")
        index[session_id] = (Path(explicit), meta)
    if session_id not in index:
        raise ValueError("No se encontro la sesion exacta; pasa --transcripcion. No se elige otra sesion por fecha")
    selected = {session_id}
    while True:
        children = {sid for sid, (_, meta) in index.items() if parent_id(meta) in selected}
        expanded = selected | children
        if expanded == selected:
            break
        selected = expanded
    return {sid: index[sid][0] for sid in sorted(selected)}, warnings


def read_usage(path):
    previous = {key: 0 for key in FIELDS}
    by_model = {}
    model = "sin_identificar"
    sample = None
    warnings = []
    seen = False
    for event in events(path):
        payload = event.get("payload", {})
        if event.get("type") == "turn_context":
            model = payload.get("model") or model
        if payload.get("type") != "token_count":
            continue
        if payload.get("rate_limits"):
            sample = {"timestamp": event.get("timestamp"), "limits": payload["rate_limits"], "source": "rollout_local"}
        info = payload.get("info") or {}
        total = info.get("total_token_usage")
        if not isinstance(total, dict):
            continue
        if not all(key in total for key in ("input_tokens", "output_tokens", "total_tokens")):
            warnings.append("Esquema de tokens incompleto; muestra ignorada")
            continue
        current = {key: int(total.get(key, 0)) for key in FIELDS}
        if current["total_tokens"] < previous["total_tokens"]:
            warnings.append("Contador reiniciado en el rollout; se suma un nuevo tramo")
            previous = {key: 0 for key in FIELDS}
        delta = {key: max(0, current[key] - previous[key]) for key in FIELDS}
        if any(delta.values()):
            row = by_model.setdefault(model, {key: 0 for key in FIELDS})
            for key in FIELDS:
                row[key] += delta[key]
        previous = current
        seen = True
    return {"models": by_model, "rate_sample": sample, "seen": seen, "warnings": warnings}


def snapshot(root, session_id, explicit=None):
    paths, warnings = session_paths(root, session_id, explicit)
    sessions = {}
    for sid, path in paths.items():
        sessions[sid] = read_usage(path)
        warnings.extend(sessions[sid]["warnings"])
    if not sessions[session_id]["seen"]:
        warnings.append("La sesion principal aun no tiene muestras de tokens")
    return {"at": now(), "sessions": sessions, "warnings": warnings,
            "rate_sample": sessions[session_id]["rate_sample"]}


def token_delta(before, after):
    result = {}
    for sid, session in after["sessions"].items():
        old_models = before["sessions"].get(sid, {}).get("models", {})
        for model, counters in session["models"].items():
            row = result.setdefault(model, {key: 0 for key in FIELDS})
            old = old_models.get(model, {})
            for key in FIELDS:
                row[key] += max(0, counters[key] - old.get(key, 0))
    return result


def windows(sample):
    if not sample:
        return {}
    limits = sample["limits"]
    if isinstance(limits, list):
        limits = next((item for item in limits if item.get("limit_id") == "codex"), {})
    if not isinstance(limits, dict):
        return {}
    return {str(value["window_minutes"]): value for key in ("primary", "secondary")
            if isinstance((value := limits.get(key)), dict) and "window_minutes" in value}


def plan_delta(before, after):
    old, new = windows(before), windows(after)
    result = {}
    for minutes, item in new.items():
        prior = old.get(minutes)
        delta = None
        reason = "sin muestra inicial"
        if prior:
            if not prior.get("resets_at") or prior.get("resets_at") != item.get("resets_at"):
                reason = "ventana reiniciada o reinicio desconocido"
            elif before["timestamp"] == after["timestamp"]:
                reason = "sin muestra nueva"
            elif item.get("used_percent") is None or prior.get("used_percent") is None:
                reason = "porcentaje no disponible"
            elif item["used_percent"] < prior["used_percent"]:
                reason = "porcentaje decreciente; diferencia no fiable"
            else:
                delta = round(item["used_percent"] - prior["used_percent"], 4)
                reason = "diferencia observada de toda la cuenta; puede incluir otras sesiones"
        result[minutes] = {"before": prior.get("used_percent") if prior else None,
                           "after": item.get("used_percent"), "delta": delta, "reason": reason,
                           "sample_at": after["timestamp"], "resets_at": item.get("resets_at"),
                           "source": after.get("source", "rollout_local")}
    return result


def apply_live_limits(current, args):
    """Valores leidos por get_usage_limits; el script no accede a autenticacion."""
    provided = {}
    for key, suffix, minutes in (("primary", "5h", 300), ("secondary", "semanal", 10080)):
        value = getattr(args, "uso_" + suffix, None)
        reset = getattr(args, "reinicio_" + suffix, None)
        if value is not None:
            if not 0 <= value <= 100 or reset is None or reset <= 0:
                raise ValueError("Un porcentaje en vivo requiere valor 0-100 y su reinicio Unix valido")
            provided[key] = {"window_minutes": minutes, "used_percent": value, "resets_at": reset}
    if provided:
        current["rate_sample"] = {"timestamp": now(), "limits": {"limit_id": "codex", **provided},
                                  "source": "codex_app_get_usage_limits"}
    return current


def dump(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, path)


@contextmanager
def lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def run(args):
    sid = args.sesion or os.environ.get("CODEX_THREAD_ID") or os.environ.get("CODEX_SESSION_ID")
    if not sid or not re.fullmatch(r"[A-Za-z0-9_-]+", sid):
        raise ValueError("Falta un identificador de sesion valido (--sesion)")
    root = Path(args.sesiones)
    folder = Path(args.registro)
    if args.fase == "estado":
        return {"session_id": sid, "snapshot": apply_live_limits(snapshot(root, sid, args.transcripcion), args)}
    state_path = folder / "sesiones" / (sid + ".json")
    with lock(folder / "registro.lock"):
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else None
        if args.fase == "inicio" and state and state["status"] == "active":
            return {"status": "ya_iniciado", "encargo": state["name"], "task_id": state["task_id"]}
        if args.fase == "fin" and state and state["status"] == "closed":
            return state["report"]
        current = apply_live_limits(snapshot(root, sid, args.transcripcion), args)
        if args.fase == "inicio":
            state = {"status": "active", "name": args.encargo or "Encargo sin titulo",
                     "session_id": sid, "task_id": str(uuid.uuid4()), "baseline": current}
            dump(state_path, state)
            return {"status": "iniciado", "encargo": state["name"], "task_id": state["task_id"],
                    "warnings": current["warnings"]}
        if not state:
            raise ValueError("No hay inicio registrado para esta sesion; no se inventa una linea base")
        models = token_delta(state["baseline"], current)
        report = {"status": "cerrado", "task_id": state["task_id"], "session_id": sid,
                  "encargo": state["name"], "inicio": state["baseline"]["at"], "fin": current["at"],
                  "models": models, "tokens_total": sum(row["total_tokens"] for row in models.values()),
                  "plan": plan_delta(state["baseline"]["rate_sample"], current["rate_sample"]),
                  "coste_api_usd": None, "estimado_plan_pct": None,
                  "warnings": sorted(set(state["baseline"]["warnings"] + current["warnings"])),
                  "limites": ["Tokens observados hasta esta lectura; la respuesta final posterior queda fuera",
                              "Coste API y porcentaje atribuible al encargo no disponibles sin tarifas/calibracion propias",
                              "Los rollouts locales pueden cambiar de formato; subagentes incluidos solo con filiacion explicita"]}
        if any(item["delta"] is not None and item["delta"] > args.limite_semanal
               for minutes, item in report["plan"].items() if minutes == "10080"):
            report["warnings"].append(f"La diferencia semanal de la cuenta supera {args.limite_semanal}%")
        archive = folder / "encargos" / (state["task_id"] + ".json")
        # El id se conserva: repetir fin no agrega otra fila.
        csv_path = folder / "uso_encargos.csv"
        columns = ("task_id", "session_id", "encargo", "inicio", "fin", "tokens_total")
        logged = set()
        if csv_path.exists():
            with csv_path.open(encoding="utf-8-sig", newline="") as stream:
                logged = {row["task_id"] for row in csv.DictReader(stream, delimiter=";")}
        if state["task_id"] not in logged:
            header = not csv_path.exists()
            with csv_path.open("a", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=columns, delimiter=";", extrasaction="ignore")
                if header:
                    writer.writeheader()
                writer.writerow(report)
        dump(archive, report)
        state.update(status="closed", report=report)
        dump(state_path, state)
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fase", required=True, choices=("inicio", "fin", "estado"))
    parser.add_argument("--encargo")
    parser.add_argument("--sesion")
    parser.add_argument("--transcripcion")
    parser.add_argument("--sesiones", default=str(Path.home() / ".codex" / "sessions"))
    parser.add_argument("--registro", default=str(CENTRAL / "registro" / "codex"))
    parser.add_argument("--limite-semanal", type=float, default=10)
    parser.add_argument("--uso-5h", type=float, help="usedPercent leido de get_usage_limits, ventana 300 min")
    parser.add_argument("--reinicio-5h", type=int, help="resetsAt Unix de esa misma muestra")
    parser.add_argument("--uso-semanal", type=float, help="usedPercent leido de get_usage_limits, ventana 10080 min")
    parser.add_argument("--reinicio-semanal", type=int, help="resetsAt Unix de esa misma muestra")
    args = parser.parse_args()
    try:
        print(json.dumps(run(args), ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
