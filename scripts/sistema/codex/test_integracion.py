"""Pruebas de consumo y controles sin llamar modelos ni abrir Rhino."""
import argparse
import base64
import csv
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from hook_equipo import decide, handle, inside
from preparar_instalacion import CENTRAL, DESTINO, prepare
from uso_encargo import apply_live_limits, plan_delta, read_usage, run, snapshot, token_delta


def append(path, *items):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        for item in items:
            stream.write(json.dumps(item) + "\n")


def meta(sid, parent=None):
    source = {"subagent": {"spawn": {"parent_thread_id": parent}}} if parent else "vscode"
    return {"type": "session_meta", "payload": {"id": sid, "source": source}}


def usage(input_tokens, cached, output, stamp="2026-11-08T12:00:00Z"):
    return {"type": "event_msg", "timestamp": stamp,
            "payload": {"type": "token_count", "info": {"total_token_usage": {
                "input_tokens": input_tokens, "cached_input_tokens": cached,
                "output_tokens": output, "reasoning_output_tokens": output // 2,
                "total_tokens": input_tokens + output}}}}


def context(model="gpt-6.1-sol"):
    return {"type": "turn_context", "payload": {"model": model}}


class Integration(unittest.TestCase):
    def setUp(self):
        self.test_root = CENTRAL.parent / "migracion-codex" / "pruebas"
        self.test_root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=self.test_root)
        self.root = Path(self.temp.name)

    def tearDown(self):
        # Verificar el destino antes del borrado recursivo de fixtures propios.
        self.root.resolve().relative_to(self.test_root.resolve())
        self.assertFalse(self.root.is_symlink())
        self.temp.cleanup()

    def test_tokens_deduplicate_samples_and_cache_is_subset(self):
        path = self.root / "root.jsonl"
        append(path, meta("root"), context(), usage(100, 60, 10), usage(100, 60, 10))
        result = read_usage(path)
        row = result["models"]["gpt-6.1-sol"]
        self.assertEqual(row["total_tokens"], 110)
        self.assertEqual(row["cached_input_tokens"], 60)
        self.assertEqual(row["reasoning_output_tokens"], 5)
        self.assertEqual(row["input_tokens"] + row["output_tokens"], 110)

    def test_delta_children_and_models_excludes_unrelated_chats(self):
        path = self.root / "root.jsonl"
        append(path, meta("root"), context(), usage(100, 60, 10))
        before = snapshot(self.root, "root")
        append(path, usage(150, 80, 20), context("gpt-6-luna"), usage(190, 100, 25))
        append(self.root / "child.jsonl", meta("child", "root"), context(), usage(30, 10, 4))
        append(self.root / "grandchild.jsonl", meta("grandchild", "child"), context(), usage(20, 0, 3))
        append(self.root / "other.jsonl", meta("other"), context(), usage(9000, 0, 100))
        result = token_delta(before, snapshot(self.root, "root"))
        self.assertEqual(result["gpt-6.1-sol"]["total_tokens"], 117)
        self.assertEqual(result["gpt-6-luna"]["total_tokens"], 45)

    def test_rate_limits_handle_resets_missing_and_stale_samples(self):
        def sample(pct, reset=100, stamp="a"):
            return {"timestamp": stamp, "limits": {"primary": {
                "window_minutes": 300, "used_percent": pct, "resets_at": reset}}}
        self.assertEqual(plan_delta(sample(10), sample(12, stamp="b"))["300"]["delta"], 2)
        self.assertIsNone(plan_delta(sample(10), sample(2, reset=200, stamp="b"))["300"]["delta"])
        self.assertIsNone(plan_delta(sample(10), sample(10))["300"]["delta"])
        self.assertIsNone(plan_delta(None, sample(10))["300"]["delta"])
        self.assertEqual(plan_delta(None, None), {})

    def test_multiple_sessions_and_repeat_finish_keep_one_csv_row(self):
        sessions, logs = self.root / "sessions", self.root / "logs"
        path = sessions / "root.jsonl"
        append(path, meta("root"), context(), usage(100, 60, 10))
        args = argparse.Namespace(sesion="root", sesiones=str(sessions), registro=str(logs),
                                  transcripcion=None, fase="inicio", encargo="A; con acento á", limite_semanal=10)
        first = run(args)
        self.assertEqual(run(args)["task_id"], first["task_id"])
        append(sessions / "other.jsonl", meta("other"), context(), usage(1000, 0, 10))
        args.sesion = "other"
        run(args)
        append(path, usage(120, 70, 15))
        args.sesion, args.fase = "root", "fin"
        report = run(args)
        self.assertEqual(report["tokens_total"], 25)
        self.assertEqual(run(args), report)
        with (logs / "uso_encargos.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream, delimiter=";"))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["encargo"], "A; con acento á")
        self.assertEqual(json.loads((logs / "sesiones" / "other.json").read_text())["status"], "active")

    def test_exact_identity_and_truncated_tail(self):
        path = self.root / "root.jsonl"
        append(path, meta("root"), context(), usage(10, 0, 1))
        with path.open("a", encoding="utf-8") as stream:
            stream.write('{"type":')
        self.assertEqual(read_usage(path)["models"]["gpt-6.1-sol"]["total_tokens"], 11)
        with self.assertRaises(ValueError):
            snapshot(self.root, "wrong", path)

    def test_live_app_limits_validate_and_record_source(self):
        args = argparse.Namespace(uso_5h=15, reinicio_5h=1794155965, uso_semanal=None, reinicio_semanal=None)
        result = apply_live_limits({}, args)["rate_sample"]
        self.assertEqual(result["source"], "codex_app_get_usage_limits")
        self.assertEqual(result["limits"]["primary"]["used_percent"], 15)
        self.assertNotIn("secondary", result["limits"])
        args.reinicio_5h = None
        with self.assertRaises(ValueError):
            apply_live_limits({}, args)

    def test_hook_denies_generic_agents_and_model_override(self):
        agents = {"critico": {"model": "gpt-6.1-sol"}}
        event = {"hook_event_name": "PreToolUse", "tool_name": "spawn_agent",
                 "tool_input": {"agent_type": "critico"}}
        self.assertIsNone(decide(event, agents))
        event["tool_input"]["model"] = "otro"
        self.assertIsNotNone(decide(event, agents))
        event["tool_input"] = {"agent_type": "worker"}
        self.assertIsNotNone(decide(event, agents))
        event["tool_input"] = {"agent_type": "explorer"}
        self.assertIsNone(decide(event, agents))

    def test_hook_scope_native_profiles_and_no_prompt_logging(self):
        target = prepare(self.root / "codex")
        event = {"hook_event_name": "PreToolUse", "tool_name": "Agent", "cwd": str(target),
                 "tool_input": {"agent_type": "critico", "message": "PRIVATE_PROMPT"}}
        logs = self.root / "logs"
        self.assertEqual(handle(event, target, logs), {})
        self.assertNotIn("PRIVATE_PROMPT", (logs / "equipo.jsonl").read_text())
        event["tool_input"]["agent_type"] = "generic"
        self.assertEqual(handle(event, target, logs)["hookSpecificOutput"]["permissionDecision"], "deny")
        event["cwd"] = str(self.root / "codex-other")
        self.assertEqual(handle(event, target, logs), {})
        self.assertFalse(inside(self.root / "codex-other", target))

    @unittest.skipUnless(os.name == "nt", "Entrada de hooks especifica de Windows")
    def test_real_windows_hook_command_from_both_shells(self):
        target = prepare(self.root / "entrada con espacios")
        config = json.loads((target / ".codex" / "hooks.json").read_text(encoding="utf-8"))
        command = config["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        command = command.replace(str(DESTINO), str(target)) + f' -Registro "{self.root / "logs"}"'
        event = {"hook_event_name": "PreToolUse", "cwd": str(target), "tool_name": "spawn_agent",
                 "tool_input": {"agent_type": "critico", "message": "Español: edición"}}
        encoded = base64.b64encode(command.encode("utf-16-le")).decode("ascii")
        for invocation, use_shell in ((command, True),
                (["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded], False)):
            result = subprocess.run(invocation, shell=use_shell, input=json.dumps(event, ensure_ascii=False),
                                    text=True, encoding="utf-8", capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout.lstrip("\ufeff")), {})
        event["tool_input"]["model"] = "otro"
        result = subprocess.run(command, shell=True, input=json.dumps(event),
                                text=True, encoding="utf-8", capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout.lstrip("\ufeff"))["hookSpecificOutput"]["permissionDecision"], "deny")


if __name__ == "__main__":
    unittest.main(verbosity=2)
