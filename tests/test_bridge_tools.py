import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS_DIR)

import claude_bridge  # noqa: E402
import repo_context  # noqa: E402


def make_project(tmp):
    os.makedirs(os.path.join(tmp, "src"))
    os.makedirs(os.path.join(tmp, "node_modules", "lib"))
    with open(os.path.join(tmp, "src", "billing.py"), "w", encoding="utf-8") as f:
        f.write("TAX_RATE = 0.2\n\nclass Invoice(Base):\n    def total(self, items, *, discount=0):\n        return 1\n\n"
                "async def fetch_invoice(invoice_id):\n    pass\n")
    with open(os.path.join(tmp, "src", "app.ts"), "w", encoding="utf-8") as f:
        f.write("export class Router {}\nexport async function handle(req: Request) {}\n"
                "export const render = (props) => null\nexport interface Props {}\n")
    with open(os.path.join(tmp, "node_modules", "lib", "index.js"), "w", encoding="utf-8") as f:
        f.write("function ignored() {}\n")
    with open(os.path.join(tmp, "logo.png"), "wb") as f:
        f.write(b"\x89PNG\x00\x00binary")


class RepoContextTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name
        make_project(self.tmp)

    def tearDown(self):
        self._tmp.cleanup()

    def test_repo_map_extracts_symbols_and_skips_vendor_and_binary(self):
        out = repo_context.build_repo_map(self.tmp)
        self.assertIn("class Invoice(Base)", out)
        self.assertIn("    def total(self, items, discount)", out)
        self.assertIn("async def fetch_invoice(invoice_id)", out)
        self.assertIn("TAX_RATE = ...", out)
        self.assertIn("export class Router", out)
        self.assertIn("export async function handle(req: Request)", out)
        self.assertIn("export const render = (props) =>", out)
        self.assertNotIn("node_modules", out)
        self.assertNotIn("logo.png", out)

    def test_focus_ranks_relevant_file_first(self):
        out = repo_context.build_repo_map(self.tmp, focus="billing invoice")
        self.assertLess(out.index("src/billing.py"), out.index("src/app.ts"))

    def test_budget_is_respected(self):
        out = repo_context.build_repo_map(self.tmp, max_chars=80)
        self.assertIn("не вошли в бюджет", out)

    def test_pack_repo_with_paths(self):
        out = repo_context.pack_repo(self.tmp, paths=["src/app.ts"])
        self.assertIn('<file path="src/app.ts">', out)
        self.assertNotIn("billing.py", out)

    def test_missing_folder(self):
        self.assertTrue(repo_context.build_repo_map("/nonexistent/xyz").startswith("REPO_ERROR"))


class OrchestrationTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        make_project(self._tmp.name)
        self.providers = {"providers": {
            "fast": {"type": "openai_compatible", "base_url": "http://x", "model": "m"},
            "down": {"type": "openai_compatible", "base_url": "http://y", "model": "m"},
        }}
        self.agents = {"agents": {
            "a": {"name": "A", "primary_provider": "fast", "fallback_providers": []},
            "b": {"name": "B", "primary_provider": "fast", "fallback_providers": []},
            "broken": {"name": "Broken", "primary_provider": "down", "fallback_providers": []},
        }}
        self.calls = []

        def fake_run(prov, prompt, system_prompt=None, timeout=60):
            self.calls.append((prov["base_url"], prompt, system_prompt))
            if prov["base_url"] == "http://y":
                return "PROVIDER_OFFLINE: нет связи"
            return f"answer#{len(self.calls)}"

        self.patches = [
            mock.patch.object(claude_bridge, "load_providers", return_value=self.providers),
            mock.patch.object(claude_bridge, "load_agents", return_value=self.agents),
            mock.patch.object(claude_bridge, "run_openai_compatible", side_effect=fake_run),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self._tmp.cleanup()

    def test_agent_run_injects_repo_map_for_api_models(self):
        claude_bridge.handle_agent_run("a", "fix invoice", work_folder=self._tmp.name)
        self.assertIn("КАРТА РЕПОЗИТОРИЯ", self.calls[0][2])
        self.assertIn("class Invoice", self.calls[0][2])

    def test_agent_run_without_context(self):
        claude_bridge.handle_agent_run("a", "x", work_folder=self._tmp.name, with_context=False)
        self.assertNotIn("КАРТА РЕПОЗИТОРИЯ", self.calls[0][2])

    def test_parallel_with_judge(self):
        out = claude_bridge.handle_agents_parallel(["a", "b", "broken"], "task", self._tmp.name, judge="a")
        self.assertEqual(len(self.calls), 4)
        judge_prompt = self.calls[-1][1]
        self.assertIn("Вариант агента 'a'", judge_prompt)
        self.assertIn("Вариант агента 'b'", judge_prompt)
        self.assertNotIn("Вариант агента 'broken'", judge_prompt)
        self.assertIn("Исходные варианты", out)

    def test_parallel_all_failed(self):
        out = claude_bridge.handle_agents_parallel("broken", "task", self._tmp.name)
        self.assertTrue(out.startswith("AGENT_ERROR"))

    def test_pipeline_passes_previous_stage_output(self):
        out = claude_bridge.handle_agent_pipeline("feature", ["a", "b"], self._tmp.name)
        self.assertIn("answer#1", self.calls[1][2])
        self.assertIn("answer#2", out)

    def test_pipeline_stops_on_failure(self):
        out = claude_bridge.handle_agent_pipeline("feature", "a,broken,b", self._tmp.name)
        self.assertTrue(out.startswith("AGENT_ERROR"))
        self.assertIn("'broken'", out)
        self.assertEqual(len(self.calls), 2)


class McpProtocolTests(unittest.TestCase):
    def test_tools_list_and_repo_map_call(self):
        reqs = [
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
             "params": {"name": "repo_map", "arguments": {"work_folder": TOOLS_DIR, "focus": "repo"}}},
        ]
        proc = subprocess.run(
            [sys.executable, os.path.join(TOOLS_DIR, "claude_bridge.py")],
            input="\n".join(json.dumps(r) for r in reqs) + "\n",
            capture_output=True, text=True, encoding="utf-8", timeout=60,
        )
        lines = [json.loads(l) for l in proc.stdout.splitlines() if l.strip()]
        names = {t["name"] for t in lines[0]["result"]["tools"]}
        self.assertTrue({"repo_map", "repo_pack", "agents_parallel", "agent_pipeline"} <= names)
        self.assertFalse(lines[1]["result"]["isError"])
        self.assertIn("def build_repo_map", lines[1]["result"]["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
