#!/usr/bin/env bash
# Exercise the pinned action against disposable git changes without API credentials.
set -euo pipefail

repo=$(cd "$(dirname "$0")/../.." && pwd)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
ref=$(sed -nE 's/.*uses: dorny\/paths-filter@([0-9a-f]{40}).*/\1/p' "$repo/.github/workflows/make-all.yml")
test "${#ref}" -eq 40
curl -fsSL "https://raw.githubusercontent.com/dorny/paths-filter/$ref/dist/index.js" -o "$scratch/action.js"

mkdir "$scratch/repo"
cd "$scratch/repo"
git init -q
git -c user.name=test -c user.email=test@example.com commit -qm base --allow-empty

run_action() {
  : > "$scratch/output"
  env INPUT_BASE=HEAD INPUT_TOKEN= INPUT_FILTERS="$1" \
    INPUT_PREDICATE-QUANTIFIER=every GITHUB_EVENT_NAME=push \
    GITHUB_OUTPUT="$scratch/output" GITHUB_WORKSPACE="$scratch/repo" \
    node "$scratch/action.js" > "$scratch/log" 2>&1 || { cat "$scratch/log"; return 1; }
}

check() {
  local name=$1 full=$2 workflow=$3
  shift 3
  git reset --hard -q HEAD
  git clean -fdq
  for file in "$@"; do
    mkdir -p "$(dirname "$file")"
    printf 'changed\n' > "$file"
    git add -- "$file"
  done
  run_action "$repo/.github/validation-paths.yml"
  test "$(awk '/^full<</ {getline; print; exit}' "$scratch/output")" = "$full"
  test "$(awk '/^workflow<</ {getline; print; exit}' "$scratch/output")" = "$workflow"
  printf 'PASS %s\n' "$name"
}

check documents false false README.md docs/guide.md elixir/docs/logging.md
check media false false .github/media/demo.jpg .github/media/demo.mp4
check unknown-media true false .github/media/script.sh
check source true false elixir/lib/new.ex
check mixed true false README.md elixir/lib/new.ex
check root-agent-guide false false AGENTS.md
check root-agent-guide-and-source true false AGENTS.md elixir/lib/new.ex
check root-agent-guide-and-workflow false true AGENTS.md elixir/WORKFLOW.md
check procedures false false .codex/skills/push/SKILL.md elixir/AGENTS.md
check workflow false true elixir/WORKFLOW.md
check workflow-and-source true true elixir/WORKFLOW.md elixir/lib/new.ex
check actions true false .github/workflows/make-all.yml
check shell true false .codex/worktree_init.sh
check dependencies true false elixir/mix.lock
check config true false elixir/.formatter.exs
check markdown-fixture true false elixir/test/fixtures/startup_workflow.md
check unknown true false new-area/guide.md
check filter true false .github/validation-paths.yml

# Deletion and renaming into the documentation allowlist must still validate source.
git -c user.name=test -c user.email=test@example.com commit -qm seed
mkdir -p elixir/lib
printf 'source\n' > elixir/lib/old.ex
git add .
git -c user.name=test -c user.email=test@example.com commit -qm source
git rm -q elixir/lib/old.ex
run_action "$repo/.github/validation-paths.yml"
test "$(awk '/^full<</ {getline; print; exit}' "$scratch/output")" = true
printf 'PASS deleted-source\n'
git reset --hard -q HEAD
git mv elixir/lib/old.ex README.md
run_action "$repo/.github/validation-paths.yml"
test "$(awk '/^full<</ {getline; print; exit}' "$scratch/output")" = true
printf 'PASS renamed-source\n'

if run_action "$scratch/missing-filter.yml" > /dev/null; then
  echo 'Missing filter unexpectedly succeeded' >&2
  exit 1
fi
printf 'PASS missing-filter-fails\n'
