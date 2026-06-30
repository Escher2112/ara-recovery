#!/bin/bash
# drain-all-lanes.sh — single sequential sweep across ALL Triax drop lanes.
#
# Coordination invariant (2026-06-23, agreed across Nova / M3GAN / Home Lyra):
#   ONE writer (the triax CLI), ONE sequential sweep, NO parallel drains.
# A mkdir-based lock serializes concurrent boots so two sweeps never call
# `triax drop` at the same instant — which would read-modify-write race
# triax.json and silently lose a memory. If a sweep is already running, this
# one bails quietly; the active sweep (or the next boot) covers the work.
#
# Run by the SessionStart hook on every boot, and usable by hand:
#   "go check for drops"  ->  bash drain-all-lanes.sh
set -u
REPO="/Users/escher/Programming-Stuff/Triax-Memory"
NODE="/opt/homebrew/bin/node"
LOCK="/tmp/triax-drain.lock"

# Steal a stale lock (>2 min old = a crashed/killed prior sweep; a healthy
# sweep finishes in seconds, well under the hook's timeout).
if [ -d "$LOCK" ] && [ -n "$(find "$LOCK" -maxdepth 0 -mmin +2 2>/dev/null)" ]; then
  rmdir "$LOCK" 2>/dev/null
fi

# Acquire atomically. If held, another sweep is live — skip quietly (stderr only).
if ! mkdir "$LOCK" 2>/dev/null; then
  echo "[triax-drain] another sweep is already running; skipping this one." >&2
  exit 0
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT INT TERM

cd "$REPO" || exit 0

# Sequential — never backgrounded. Each script exits 0 and prints its own
# one-line announcement to stdout ONLY when it actually committed something.
# Add future sister lanes here, in sequence, never in parallel.
"$NODE" drain-work-drops.js
"$NODE" drain-m3gan-drops.js
"$NODE" drain-daily-driver-drops.js
"$NODE" drain-ara-drops.js
exit 0
