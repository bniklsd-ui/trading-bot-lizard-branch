#!/usr/bin/env bash
#
# install_hooks.sh — tracked installer for the .git/hooks/pre-commit doc-rotation
# hook (P14-F Mini-Plan, 2026-08-31). Copies the canonical hook body from this
# file into ``.git/hooks/pre-commit`` and chmods it +x.
#
# — Idempotent: a second run is a no-op (hook already installed with the same
#   body → exit 0; hook exists with different body → exit 1 with diagnostic).
# — Touches ONLY ``.git/hooks/pre-commit``; never any tracked file.
# — Run from anywhere: REPO_ROOT is inferred from the script's own location.
# — Designed to be invoked as the last step of ``scripts/dev_install.sh``
#   (D3), so a fresh clone / fresh venv gets the hook automatically.
#
# Usage:
#   bash scripts/install_hooks.sh                 # install (idempotent)
#   bash scripts/install_hooks.sh --dry-run       # preview without writing
#
# Exit codes:
#   0 — installed or already up-to-date
#   1 — existing hook differs from this canonical body (operator decision needed)
#   2 — I/O error (no .git/, no write permission, …)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
HOOK_PATH="${REPO_ROOT}/.git/hooks/pre-commit"
CANONICAL_BODY="$(cat <<'HOOK_BODY'
#!/bin/sh
# Pre-commit hook: doc-rotation hygiene check.
# Three steps (P14-F + P16-F9, 2026-09-08):
#   Step 1: no phase CLAUDE.md carries more than one "## Session stopped"
#           block (Doc-Layers-Konvention, root CLAUDE.md "Rotation rule").
#   Step 2: head-N == archive-max-(N-1) (archive-sequence integrity).
#           Step 2 became default in Mini-Session 24 (2026-08-31) after
#           D5-Beweis (Mini-Sessions 22+23 verifiziert: alle 14 Archive
#           Step-2-konform).
#   Step 3: archive numbers are contiguous 1..head_max-1 (P16-F9, Nikinger
#           2026-09-08). Diese Prüfung ist eine Verschärfung von Step 2: ein
#           Archiv mit ``#16, #14, …, #1`` (Lücke bei #15) bestünde Step 2
#           (head=17 → expected=16 = OK), aber Step 3 macht den Drift laut.
#           Genau diese Lücke ist in Session #17 (F8) operativ aufgetreten
#           und blieb drei Sessions lang unentdeckt.
# Installed by scripts/install_hooks.sh (P14-F, 2026-08-31, +P16-F9 2026-09-08).
# Tracked source: scripts/install_hooks.sh — re-run after every ``git clone`` /
# fresh venv setup (or just re-run ``bash scripts/dev_install.sh`` which
# calls this at the end).
#
# Override per commit with `git commit --no-verify` when needed (z. B. wenn
# ein F9-Befund absichtlich noch nicht repariert ist, siehe Doc-Drift-Audit
# Phase 16 Folgesession).

if ! command -v python3 >/dev/null 2>&1; then
    echo "pre-commit: python3 not found, skipping doc-rotation check"
    exit 0
fi

if [ ! -f scripts/check_doc_rotation.py ]; then
    echo "pre-commit: scripts/check_doc_rotation.py missing, skipping"
    exit 0
fi

# Step 2 became default after D5-Beweis (Mini-Session 24, 2026-08-31).
# Step 3 became default with F9 (P16, 2026-09-08, Nikinger-Freigabe).
python3 scripts/check_doc_rotation.py --strict --quiet
result=$?

if [ $result -ne 0 ]; then
    echo ""
    echo "pre-commit: doc-rotation check failed (exit $result)."
    echo "  Run 'python3 scripts/check_doc_rotation.py' for details."
    echo "  Use 'git commit --no-verify' to override if you know what you are doing."
fi

exit $result
HOOK_BODY
)"

DRY_RUN=0
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        *) echo "install_hooks: unknown arg: $arg" >&2; exit 2 ;;
    esac
done

if [[ ! -d "${REPO_ROOT}/.git" ]]; then
    echo "install_hooks: no .git/ at ${REPO_ROOT} — not a git checkout?" >&2
    exit 2
fi

if [[ -f "${HOOK_PATH}" ]]; then
    existing="$(cat "${HOOK_PATH}")"
    if [[ "${existing}" == "${CANONICAL_BODY}" ]]; then
        echo "install_hooks: hook already up-to-date at ${HOOK_PATH}"
        exit 0
    else
        echo "install_hooks: existing hook at ${HOOK_PATH} differs from canonical body" >&2
        echo "  Diff:" >&2
        diff <(echo "${existing}") <(echo "${CANONICAL_BODY}") >&2 || true
        echo "" >&2
        echo "  Decision required: review the diff, then either:" >&2
        echo "    (a) keep the existing hook and skip this installer," >&2
        echo "    (b) back up the existing hook (mv .git/hooks/pre-commit{,.bak})" >&2
        echo "        and re-run this script." >&2
        exit 1
    fi
fi

if [[ "${DRY_RUN}" == "1" ]]; then
    echo "install_hooks: (dry-run) would write ${HOOK_PATH} (${#CANONICAL_BODY} bytes)"
    exit 0
fi

echo "${CANONICAL_BODY}" > "${HOOK_PATH}"
chmod +x "${HOOK_PATH}"
echo "install_hooks: hook installed at ${HOOK_PATH} (${#CANONICAL_BODY} bytes)"