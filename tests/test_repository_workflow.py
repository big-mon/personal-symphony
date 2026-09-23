"""Exercise the exact WORKFLOW bootstrap with real disposable Git repositories."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

WORKFLOW = Path(__file__).resolve().parents[1] / "WORKFLOW.md"
CODE = WORKFLOW.read_text().split("```python\n", 1)[1].split("\n```", 1)[0]
MODULE = {"__name__": "repository_workflow"}
exec(compile(CODE, str(WORKFLOW), "exec"), MODULE)
REAL_GIT = MODULE["git"]


class Routing(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="repository-routing-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.cwd = Path.cwd()
        self.addCleanup(os.chdir, self.cwd)
        self.addCleanup(MODULE.update, git=REAL_GIT)
        self.sources = []
        for name in ("alpha", "beta"):
            source = self.root / name
            source.mkdir()
            REAL_GIT(source, "init", "-b", "main")
            (source / "README.md").write_text(name)
            REAL_GIT(source, "add", "README.md")
            REAL_GIT(source, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                     "commit", "-m", "fixture")
            REAL_GIT(source, "remote", "add", "origin", f"https://github.com/example/{name}.git")
            self.sources.append(source)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        os.chdir(self.workspace)

        def fixture_transport(cwd, *args):
            # Only test transport changes: validation still sees real Git config.
            if args[0] == "clone":
                url, destination = args[2:]
                source = self.sources[0 if "/alpha.git" in url else 1]
                result = REAL_GIT(cwd, "clone", "--", str(source), destination)
                REAL_GIT(destination, "remote", "set-url", "origin", url)
                return result
            if args[0] == "ls-remote":
                return REAL_GIT(cwd, "ls-remote", "--exit-code", str(self.sources[0]), "HEAD")
            return REAL_GIT(cwd, *args)
        MODULE["git"] = fixture_transport

    def snapshot(self, index=0):
        label = {"id": f"label-{index}", "name": "untrusted display name", "description": str(self.sources[index]),
                 "isGroup": False, "archivedAt": None,
                 "parent": {"id": "group", "name": "Repository", "isGroup": True, "archivedAt": None}}
        issue_id = "11111111-1111-4111-8111-111111111111"
        return {"issue_id": issue_id, "pages": [{"cursor": None, "response": {"data": {"issue": {
            "id": issue_id, "updatedAt": "2026-01-01T00:00:00Z", "state": {"name": "Todo"},
            "labels": {"nodes": [label], "pageInfo": {"hasNextPage": False, "endCursor": "last"}}}}}}]}

    def labels(self, snapshot):
        return snapshot["pages"][0]["response"]["data"]["issue"]["labels"]

    def run_gate(self, snapshot):
        with contextlib.redirect_stdout(io.StringIO()):
            return MODULE["bootstrap"](snapshot)

    def test_two_targets_retry_and_changed_label(self):
        before = [REAL_GIT(s, "status", "--porcelain") for s in self.sources]
        first = self.run_gate(self.snapshot())
        checkout = self.workspace / "repo"
        (checkout / "unfinished.txt").write_text("preserve me")
        head = REAL_GIT(checkout, "rev-parse", "HEAD")
        self.assertEqual(first, self.run_gate(self.snapshot()))
        self.assertEqual(head, REAL_GIT(checkout, "rev-parse", "HEAD"))
        with self.assertRaisesRegex(ValueError, "Repository changed"):
            self.run_gate(self.snapshot(1))
        self.assertEqual("preserve me", (checkout / "unfinished.txt").read_text())
        second_workspace = self.root / "workspace-two"
        second_workspace.mkdir()
        os.chdir(second_workspace)
        second = self.run_gate(self.snapshot(1))
        self.assertNotEqual(first["repository"], second["repository"])
        self.assertEqual("beta", (second_workspace / "repo/README.md").read_text())
        self.assertEqual(before, [REAL_GIT(s, "status", "--porcelain") for s in self.sources])

    def test_missing_ambiguous_invalid_and_injection(self):
        base = self.snapshot()
        cases = []
        missing = copy.deepcopy(base)
        self.labels(missing)["nodes"] = []
        cases.append(missing)
        ambiguous = copy.deepcopy(base)
        self.labels(ambiguous)["nodes"].extend(self.labels(self.snapshot(1))["nodes"])
        cases.append(ambiguous)
        for value in (None, "", "relative/path", str(self.sources[0]) + ";touch INJECTED",
                      "$(touch INJECTED)", str(self.root / "absent"), "https://github.com/example/alpha"):
            item = copy.deepcopy(base)
            self.labels(item)["nodes"][0]["description"] = value
            cases.append(item)
        for item in cases:
            with self.subTest(item=item), self.assertRaises((ValueError, OSError)):
                self.run_gate(item)
            self.assertFalse((self.workspace / "repo").exists())
            self.assertFalse((self.workspace / ".repository-binding.json").exists())
        self.assertFalse((self.workspace / "INJECTED").exists())

    def test_pagination_and_partial_failures(self):
        snapshot = self.snapshot()
        first = self.labels(snapshot)
        second_page = copy.deepcopy(snapshot["pages"][0])
        second_page["cursor"] = "next"
        first["nodes"] = []
        first["pageInfo"] = {"hasNextPage": True, "endCursor": "next"}
        with self.assertRaisesRegex(ValueError, "incomplete"):
            self.run_gate(snapshot)
        snapshot["pages"].append(second_page)
        for failure in ("errors", "cursor", "revision", "null_issue", "missing_info"):
            broken = copy.deepcopy(snapshot)
            response = broken["pages"][1]["response"]
            if failure == "errors":
                response["errors"] = [{"message": "partial data"}]
            elif failure == "cursor":
                broken["pages"][1]["cursor"] = "wrong"
            elif failure == "revision":
                response["data"]["issue"]["updatedAt"] = "changed"
            elif failure == "null_issue":
                response["data"]["issue"] = None
            else:
                del response["data"]["issue"]["labels"]["pageInfo"]
            with self.subTest(failure=failure), self.assertRaises((ValueError, KeyError, TypeError)):
                self.run_gate(broken)
            self.assertFalse((self.workspace / "repo").exists())
        self.assertEqual("example/alpha", self.run_gate(snapshot)["repository"])

    def test_origin_changes_and_unsafe_origins(self):
        for value in ("https://token@github.com/example/alpha", "ext::touch INJECTED", "/local/path",
                      "https://other.invalid/example/alpha", "git@github.com:owner/.."):
            REAL_GIT(self.sources[0], "remote", "set-url", "origin", value)
            with self.assertRaises(ValueError):
                self.run_gate(self.snapshot())
            self.assertFalse((self.workspace / "repo").exists())
        REAL_GIT(self.sources[0], "remote", "set-url", "origin", "https://github.com/example/alpha.git")
        self.run_gate(self.snapshot())
        REAL_GIT(self.workspace / "repo", "remote", "set-url", "origin", "https://github.com/example/beta.git")
        with self.assertRaisesRegex(ValueError, "checkout origin"):
            self.run_gate(self.snapshot())
        REAL_GIT(self.sources[0], "config", "remote.origin.pushurl", "https://github.com/example/beta.git")
        with self.assertRaisesRegex(ValueError, "fetch/push differ"):
            self.run_gate(self.snapshot())

    def test_legacy_unbound_and_partial_clones_stop(self):
        (self.workspace / ".git").mkdir()
        with self.assertRaisesRegex(ValueError, "legacy"):
            self.run_gate(self.snapshot())
        (self.workspace / ".git").rmdir()
        (self.workspace / "repo").mkdir()
        with self.assertRaisesRegex(ValueError, "unbound"):
            self.run_gate(self.snapshot())
        (self.workspace / "repo").rmdir()
        git = MODULE["git"]
        def failed_clone(cwd, *args):
            if args[0] == "clone":
                Path(args[-1]).mkdir()
                raise ValueError("clone failed")
            return git(cwd, *args)
        MODULE["git"] = failed_clone
        with self.assertRaisesRegex(ValueError, "clone failed"):
            self.run_gate(self.snapshot())
        MODULE["git"] = git
        self.assertTrue((self.workspace / ".repository-binding.json").exists())
        with self.assertRaisesRegex(ValueError, "incomplete"):
            self.run_gate(self.snapshot())

    def test_access_failure_retains_binding_and_work(self):
        self.run_gate(self.snapshot())
        checkout = self.workspace / "repo"
        (checkout / "unfinished.txt").write_text("keep")
        binding = (self.workspace / ".repository-binding.json").read_bytes()
        git = MODULE["git"]
        def inaccessible(cwd, *args):
            if args[0] == "ls-remote":
                raise ValueError("Git operation failed (details withheld)")
            return git(cwd, *args)
        MODULE["git"] = inaccessible
        with self.assertRaisesRegex(ValueError, "Git operation failed"):
            self.run_gate(self.snapshot())
        self.assertEqual(binding, (self.workspace / ".repository-binding.json").read_bytes())
        self.assertEqual("keep", (checkout / "unfinished.txt").read_text())
        MODULE["git"] = git
        REAL_GIT(self.sources[0], "remote", "set-url", "origin", "https://github.com/example/beta.git")
        with self.assertRaisesRegex(ValueError, "Repository changed"):
            self.run_gate(self.snapshot())

    def test_untrusted_structure_and_symlinks(self):
        for field in ("archived", "group", "issue", "duplicate"):
            snapshot = self.snapshot()
            node = self.labels(snapshot)["nodes"][0]
            if field == "archived":
                node["archivedAt"] = "2026-01-01"
            elif field == "group":
                node["parent"]["isGroup"] = False
            elif field == "issue":
                snapshot["pages"][0]["response"]["data"]["issue"]["id"] = "wrong"
            else:
                self.labels(snapshot)["nodes"].append(copy.deepcopy(node))
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.run_gate(snapshot)
            self.assertFalse((self.workspace / "repo").exists())
        (self.workspace / "repo").symlink_to(self.sources[0], target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.run_gate(self.snapshot())

    def test_cli_redacts_untrusted_input(self):
        snapshot = self.snapshot()
        snapshot["pages"][0]["response"]["errors"] = [{"message": "SECRET_CANARY"}]
        result = subprocess.run(["python3", "-c", CODE], input=json.dumps(snapshot), text=True, capture_output=True)
        self.assertEqual(1, result.returncode)
        self.assertNotIn("SECRET_CANARY", result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
