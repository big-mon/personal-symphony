import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def git(cwd, *args):
    result = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True,
                            text=True, timeout=120)
    require(result.returncode == 0, "Git operation failed (details withheld)")
    return result.stdout.strip()


def origin(cwd):
    # Expanded fetch AND push URLs catch multiple remotes and URL rewrites.
    fetch = git(cwd, "remote", "get-url", "--all", "origin")
    push = git(cwd, "remote", "get-url", "--push", "--all", "origin")
    require(fetch == push, "origin fetch/push differ")
    match = re.fullmatch(r"(?:https://github\.com/|git@github\.com:)([A-Za-z0-9_-]+)/([A-Za-z0-9_.-]+)", fetch)
    require(match is not None, "origin must be one credential-free GitHub URL")
    owner, repo = match.groups()
    repo = repo.removesuffix(".git")
    require(repo not in ("", ".", ".."), "invalid repository name")
    return fetch, f"{owner}/{repo}"


def bootstrap(snapshot):
    issue_id = snapshot["issue_id"]
    uuid.UUID(issue_id)
    pages = snapshot["pages"]
    require(bool(pages), "missing label pages")
    cursor, version, nodes, seen = None, None, [], set()
    for index, page in enumerate(pages):
        require(page["cursor"] == cursor, "label page cursor mismatch")
        response = page["response"]
        require(not response.get("errors"), "GraphQL errors; snapshot rejected")
        issue = response["data"]["issue"]
        require(issue["id"] == issue_id, "issue mismatch")
        stamp = issue["updatedAt"]
        require(isinstance(stamp, str) and bool(stamp), "missing issue revision")
        require(version is None or stamp == version, "issue changed during pagination")
        version = stamp
        labels = issue["labels"]
        for node in labels["nodes"]:
            require(node["id"] not in seen, "duplicate label across pages")
            seen.add(node["id"])
            nodes.append(node)
        info = labels["pageInfo"]
        require(type(info["hasNextPage"]) is bool, "missing pagination status")
        require(info["hasNextPage"] == (index < len(pages) - 1), "incomplete or extra label pages")
        if info["hasNextPage"]:
            next_cursor = info["endCursor"]
            require(isinstance(next_cursor, str) and next_cursor and
                    next_cursor not in [p["cursor"] for p in pages[:index + 1]], "invalid label cursor")
            cursor = next_cursor
    selected = [n for n in nodes if n["parent"] and n["parent"]["name"] == "Repository"]
    require(len(selected) == 1, "expected exactly one Repository child label")
    label = selected[0]
    parent = label["parent"]
    require(parent["isGroup"] is True and label["isGroup"] is False and
            parent["archivedAt"] is None and label["archivedAt"] is None, "invalid/archived Repository label")
    name = label["name"]
    require(isinstance(name, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name),
            "Repository label must be a single directory name")
    repositories = (Path.home() / "Repos").resolve(strict=True)
    source = (repositories / name).resolve(strict=True)
    require(source.parent == repositories, "repository path escapes ~/Repos")
    require(source.is_dir() and Path(git(source, "rev-parse", "--show-toplevel")).resolve() == source,
            "registered path must be the Git repository root")
    url, slug = origin(source)
    root = Path.cwd().resolve()
    require(not root.is_relative_to(source) and not source.is_relative_to(root), "source/workspace overlap")
    binding = {"issue_id": issue_id, "label_id": label["id"], "parent_id": parent["id"],
               "label_name": name, "source": str(source), "origin": url, "repository": slug}
    marker = root / ".repository-binding.json"
    checkout = root / "repo"
    require(not marker.is_symlink() and not checkout.is_symlink(), "symlink binding/checkout rejected")
    # Existing root clones predate routing. Do not silently adopt their work.
    require(not (root / ".git").exists(), "legacy root clone needs human migration")
    if marker.exists():
        require(json.loads(marker.read_text()) == binding, "Repository changed; existing workspace retained")
    else:
        require(not checkout.exists(), "unbound checkout needs human inspection")
        with marker.open("x") as output:
            json.dump(binding, output, sort_keys=True)
            output.flush()
            os.fsync(output.fileno())
    if not checkout.exists():
        git(root, "clone", "--", url, str(checkout))
    require((checkout / ".git").is_dir() and not (checkout / ".git").is_symlink(), "incomplete/linked clone")
    require(Path(git(checkout, "rev-parse", "--show-toplevel")).resolve() == checkout, "checkout root mismatch")
    require(origin(checkout) == (url, slug), "checkout origin differs from binding")
    # Recheck access on reuse too. An empty remote has no refs or HEAD yet.
    refs = git(checkout, "ls-remote", "origin")
    if refs:
        git(checkout, "rev-parse", "--verify", "HEAD")
    else:
        require(git(checkout, "symbolic-ref", "HEAD").startswith("refs/heads/"), "invalid unborn checkout")
    print(json.dumps({"repository": slug, "checkout": str(checkout), "binding": str(marker)}))
    return binding


if __name__ == "__main__":
    try:
        bootstrap(json.load(sys.stdin))
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as error:
        # Never echo label values, arbitrary URLs, Git stderr or credentials.
        print("Repository gate blocked: " + (str(error) if type(error) is ValueError else type(error).__name__), file=sys.stderr)
        sys.exit(1)
