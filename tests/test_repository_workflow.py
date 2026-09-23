"""Exercise repository routing with real disposable Git repositories."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/repository_bootstrap.py"
sys.path.insert(0, str(SCRIPT.parent))
import repository_bootstrap as routing

REAL_GIT = routing.git
ISSUE_ID = "11111111-1111-4111-8111-111111111111"


class Routing(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="repository-routing-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.cwd = Path.cwd()
        self.addCleanup(os.chdir, self.cwd)
        self.addCleanup(setattr, routing, "git", REAL_GIT)
        home = self.root / "home"
        (home / "Repos").mkdir(parents=True)
        home_patch = patch.object(Path, "home", return_value=home)
        home_patch.start()
        self.addCleanup(home_patch.stop)
        self.sources = []
        for name in ("alpha", "beta"):
            source = home / "Repos" / name
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
                url = REAL_GIT(cwd, "remote", "get-url", "origin")
                source = self.sources[0 if "/alpha.git" in url else 1]
                return REAL_GIT(cwd, "ls-remote", str(source))
            return REAL_GIT(cwd, *args)
        routing.git = fixture_transport

    def snapshot(self, index=0):
        label = {"id": f"label-{index}", "name": self.sources[index].name,
                 "isGroup": False, "archivedAt": None,
                 "parent": {"id": "group", "name": "Repository", "isGroup": True, "archivedAt": None}}
        return {"issue_id": ISSUE_ID, "pages": [{"cursor": None, "response": {"data": {"issue": {
            "id": ISSUE_ID, "updatedAt": "2026-01-01T00:00:00Z", "state": {"name": "Todo"},
            "labels": {"nodes": [label], "pageInfo": {"hasNextPage": False, "endCursor": "last"}}}}}}]}

    def labels(self, snapshot):
        return snapshot["pages"][0]["response"]["data"]["issue"]["labels"]

    def run_gate(self, snapshot):
        with contextlib.redirect_stdout(io.StringIO()):
            return routing.bootstrap(snapshot, ISSUE_ID)

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

    def test_other_issue_snapshot_cannot_bind_or_replace_workspace(self):
        snapshot = self.snapshot(1)
        other_id = "22222222-2222-4222-8222-222222222222"
        snapshot["issue_id"] = other_id
        snapshot["pages"][0]["response"]["data"]["issue"]["id"] = other_id
        with self.assertRaisesRegex(ValueError, "dispatched issue"):
            self.run_gate(snapshot)
        self.assertFalse((self.workspace / "repo").exists())
        self.assertFalse((self.workspace / ".repository-binding.json").exists())
        for args in ([], ["not-a-uuid"], [ISSUE_ID]):
            result = subprocess.run([sys.executable, str(SCRIPT), *args],
                                    input=json.dumps(snapshot), text=True, capture_output=True)
            self.assertEqual(1, result.returncode)
            self.assertFalse((self.workspace / "repo").exists())
            self.assertFalse((self.workspace / ".repository-binding.json").exists())
        self.run_gate(self.snapshot())
        marker = self.workspace / ".repository-binding.json"
        before = marker.read_bytes()
        with self.assertRaisesRegex(ValueError, "dispatched issue"):
            self.run_gate(snapshot)
        self.assertEqual(before, marker.read_bytes())

    def test_slow_clone_has_a_longer_budget_than_metadata(self):
        run = subprocess.run
        budgets = {}
        def slow_clone(command, **kwargs):
            operation = command[3]
            budgets[operation] = kwargs["timeout"]
            # Simulate a clone needing 121 seconds without a wall-clock wait.
            if operation == "clone" and kwargs["timeout"] < 121:
                raise subprocess.TimeoutExpired(command, kwargs["timeout"])
            return run(command, **kwargs)
        with patch.object(routing.subprocess, "run", side_effect=slow_clone):
            self.run_gate(self.snapshot())
        self.assertTrue((self.workspace / "repo/.git").is_dir())
        self.assertEqual(120, budgets["remote"])
        self.assertLessEqual(budgets["clone"], 900)

    def test_missing_ambiguous_invalid_and_injection(self):
        base = self.snapshot()
        cases = []
        missing = copy.deepcopy(base)
        self.labels(missing)["nodes"] = []
        cases.append(missing)
        ambiguous = copy.deepcopy(base)
        self.labels(ambiguous)["nodes"].extend(self.labels(self.snapshot(1))["nodes"])
        cases.append(ambiguous)
        for value in (None, "", ".", "..", "../alpha", "/alpha", "owner/alpha",
                      "alpha;touch INJECTED", "$(touch INJECTED)", "absent"):
            item = copy.deepcopy(base)
            self.labels(item)["nodes"][0]["name"] = value
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
        git = routing.git
        def failed_clone(cwd, *args):
            if args[0] == "clone":
                Path(args[-1]).mkdir()
                raise ValueError("clone failed")
            return git(cwd, *args)
        routing.git = failed_clone
        with self.assertRaisesRegex(ValueError, "clone failed"):
            self.run_gate(self.snapshot())
        routing.git = git
        self.assertTrue((self.workspace / ".repository-binding.json").exists())
        with self.assertRaisesRegex(ValueError, "incomplete"):
            self.run_gate(self.snapshot())

    def test_access_failure_retains_binding_and_work(self):
        self.run_gate(self.snapshot())
        checkout = self.workspace / "repo"
        (checkout / "unfinished.txt").write_text("keep")
        binding = (self.workspace / ".repository-binding.json").read_bytes()
        git = routing.git
        def inaccessible(cwd, *args):
            if args[0] == "ls-remote":
                raise ValueError("Git operation failed (details withheld)")
            return git(cwd, *args)
        routing.git = inaccessible
        with self.assertRaisesRegex(ValueError, "Git operation failed"):
            self.run_gate(self.snapshot())
        self.assertEqual(binding, (self.workspace / ".repository-binding.json").read_bytes())
        self.assertEqual("keep", (checkout / "unfinished.txt").read_text())
        routing.git = git
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

    def test_custom_active_state_and_empty_remote(self):
        snapshot = self.snapshot()
        snapshot["pages"][0]["response"]["data"]["issue"]["state"]["name"] = "In Development"
        REAL_GIT(self.sources[0], "update-ref", "-d", "refs/heads/main")
        binding = self.run_gate(snapshot)
        self.assertEqual(binding, self.run_gate(snapshot))
        self.assertEqual("", REAL_GIT(self.workspace / "repo", "for-each-ref", "--format=%(refname)"))
        self.assertTrue(REAL_GIT(self.workspace / "repo", "symbolic-ref", "HEAD").startswith("refs/heads/"))

    def test_description_is_ignored_and_source_cannot_escape_repos(self):
        snapshot = self.snapshot()
        self.labels(snapshot)["nodes"][0]["description"] = "$(touch INJECTED); /wrong/path"
        binding = self.run_gate(snapshot)
        self.assertEqual(str(self.sources[0]), binding["source"])
        self.assertNotIn("description", binding)
        self.assertFalse((self.workspace / "INJECTED").exists())
        outside = self.root / "outside"
        outside.mkdir()
        link = self.sources[0].parent / "escape"
        link.symlink_to(outside, target_is_directory=True)
        self.labels(snapshot)["nodes"][0]["name"] = "escape"
        with self.assertRaisesRegex(ValueError, "escapes"):
            self.run_gate(snapshot)

    def test_cli_redacts_untrusted_input(self):
        snapshot = self.snapshot()
        snapshot["pages"][0]["response"]["errors"] = [{"message": "SECRET_CANARY"}]
        result = subprocess.run([sys.executable, str(SCRIPT), ISSUE_ID], input=json.dumps(snapshot), text=True, capture_output=True)
        self.assertEqual(1, result.returncode)
        self.assertNotIn("SECRET_CANARY", result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
