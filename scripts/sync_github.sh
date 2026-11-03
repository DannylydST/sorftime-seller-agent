#!/usr/bin/env bash
# Sync all GitHub distribution targets after a release.
# Targets: origin/channel -> origin/main -> cn/channel -> cn/main (main branches are mirrors of channel).
# Self-heals "main-first" commits (web edits, direct PRs into main) by reconciling them into channel first.
# About metadata (description counts) is maintained separately per GITHUB-MAINTENANCE.md section 2.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 2

fail=0
echo "[0] reconcile: pull any main-first commits into channel"
git fetch origin || fail=1
if git rev-parse -q --verify origin/main >/dev/null; then
  if [ "$(git rev-parse channel)" != "$(git merge-base channel origin/main)" ] \
     && [ "$(git rev-parse origin/main)" != "$(git merge-base channel origin/main)" ]; then
    # both sides have unique commits -> real merge needed
    if ! git merge origin/main -m "merge: reconcile main-first commits into channel (see GITHUB-MAINTENANCE section 0)"; then
      echo "[warn] merge conflict main->channel — resolve manually, then rerun"; git merge --abort 2>/dev/null; exit 1
    fi
  elif [ "$(git rev-parse origin/main)" != "$(git merge-base channel origin/main)" ]; then
    # main ahead only -> fast-forward channel
    git merge --ff-only origin/main || fail=1
  fi
fi

echo "[1/4] push origin/channel"
git push origin channel || fail=1

echo "[2/4] fast-forward origin/main (public mirror, protected branch)"
git push origin channel:main \
  || echo "[warn] origin/main rejected — lift protection, push, restore (GITHUB-MAINTENANCE.md section 0)"

echo "[3/4] push cn/channel"
git push cn channel || fail=1

echo "[4/4] fast-forward cn/main"
git push cn channel:main \
  || echo "[warn] cn/main rejected — if not fast-forwardable, sync manually (GITHUB-MAINTENANCE.md section 0)"

echo "--- remote tips (all four must point at the same commit) ---"
git ls-remote origin refs/heads/channel refs/heads/main
git ls-remote cn refs/heads/channel refs/heads/main
exit $fail
