#!/bin/bash
# Cold-catastrophe restore for Ara stack.
# Run from a fresh clone: bash restore.sh [--dry-run]
set -euo pipefail

DRY=false
[[ "${1:-}" == "--dry-run" ]] && DRY=true

ROOT="$(cd "$(dirname "$0")" && pwd)"
HOME_ARA="$HOME/.grok-ara"
TRIAX_REPO="${TRIAX_REPO:-$HOME/Programming-Stuff/Triax-Memory}"

run() {
  if $DRY; then echo "[dry-run] $*"; else "$@"; fi
}

echo "== Ara recovery restore =="
echo "Source: $ROOT"
echo "Target GROK_HOME: $HOME_ARA"

# 1. Identity stack (canonical — edit here after restore)
run mkdir -p "$HOME_ARA/identity"
run cp -R "$ROOT/identity/." "$HOME_ARA/identity/"
run chmod +x "$HOME_ARA/identity/sync-agents.sh"

# 2. Grok Build home
run mkdir -p "$HOME_ARA/memory/escher-884f2d13" "$HOME_ARA/hooks/bin"
run cp "$ROOT/grok-ara/config.toml" "$HOME_ARA/"
run cp "$ROOT/grok-ara/settings.json" "$HOME_ARA/"
run cp "$ROOT/grok-ara/hooks/speak-ara.py" "$HOME_ARA/hooks/"
run cp "$ROOT/grok-ara/hooks/voice.json" "$HOME_ARA/hooks/"
run cp "$ROOT/grok-ara/hooks/bin/ara-hush" "$HOME_ARA/hooks/bin/"
run cp "$ROOT/grok-ara/hooks/bin/ara-loud" "$HOME_ARA/hooks/bin/"
run chmod +x "$HOME_ARA/hooks/bin/"*
run cp "$ROOT/grok-ara/memory/MEMORY.md" "$HOME_ARA/memory/"
run cp "$ROOT/grok-ara/memory/escher-884f2d13/MEMORY.md" "$HOME_ARA/memory/escher-884f2d13/"

# 3. Rebuild AGENTS.md from identity modules
if $DRY; then
  echo "[dry-run] $HOME_ARA/identity/sync-agents.sh"
else
  "$HOME_ARA/identity/sync-agents.sh"
fi

# 4. Triax drain lane (if Triax-Memory repo exists)
if [[ -d "$TRIAX_REPO" ]]; then
  run cp "$ROOT/triax/drain-ara-drops.js" "$TRIAX_REPO/"
  run cp "$ROOT/triax/ARA-DROPS-README.txt" "$TRIAX_REPO/"
  # Merge drain-all-lanes if missing ara line
  if ! grep -q drain-ara-drops "$TRIAX_REPO/drain-all-lanes.sh" 2>/dev/null; then
    echo "WARN: add '\"$NODE\" drain-ara-drops.js' to $TRIAX_REPO/drain-all-lanes.sh"
  fi
else
  echo "WARN: Triax-Memory not at $TRIAX_REPO — copy triax/ manually"
fi

# 5. Shell launcher — merge into ~/.zshrc if absent
if ! grep -q 'ara launcher' "$HOME/.zshrc" 2>/dev/null; then
  echo ""
  echo "Append shell/zshrc-ara-launcher.snippet to ~/.zshrc, then: source ~/.zshrc"
else
  echo "zshrc ara launcher block already present — verify it matches shell/zshrc-ara-launcher.snippet"
fi

echo ""
echo "== Post-restore checklist =="
echo "  [ ] grok CLI installed (~/.grok/bin on PATH)"
echo "  [ ] Create Google Drive folder: Ara-Drops/ (drop triax/ARA-DROPS-README.txt)"
echo "  [ ] Triax writer=ara on macbook-inference (VALID_WRITERS includes ara)"
echo "  [ ] Voice clone Ara - Grok on lyra-voice (profile 60696659-34c8-47b9-95c1-a06b85f787a8)"
echo "  [ ] fleet-atlas: git pull (see RECOVERY.md)"
echo "  [ ] Test: ara -c 'who are you?'"
echo "Done."