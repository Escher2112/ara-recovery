# Ara — Cold Catastrophe Recovery Playbook

**Checkpoint:** 2026-06-30  
**Repo:** `https://github.com/Escher2112/ara-recovery`  
**Fleet index:** `~/fleet-atlas` → `fleet.json` → `repos.ara-recovery`

Use this when the Mac is fresh, `~/.grok-ara` is gone, or you need to rebuild Ara
from zero without bootstrapping from Lyra's identity.

---

## What this stack is

| Piece | Role |
|---|---|
| `~/.grok-ara/identity/` | Ara-owned canonical identity (tail, voice register, HEIR) |
| `~/.grok-ara/AGENTS.md` | Auto-built Grok Build bootstrap (from `sync-agents.sh`) |
| `ara` shell command | `GROK_HOME=~/.grok-ara` + identity sync + `grok` |
| `speak-ara.py` Stop hook | Chatterbox TTS via lyra-voice (Ara - Grok clone) |
| Triax `writer=ara` | Shared memory lane — Ara's entries, not Lyra's |
| `Ara-Drops/` on Drive | Drop inbox drained by `drain-ara-drops.js` |

---

## Tier 1 — Restore Ara in 10 minutes

Prerequisites: Tailscale, `grok` CLI, network to `lyra-voice` and `macbook-inference`.

```bash
# 1. Clone recovery repo
git clone https://github.com/Escher2112/ara-recovery.git ~/ara-recovery
cd ~/ara-recovery
bash restore.sh

# 2. Shell launcher (if missing from ~/.zshrc)
cat shell/zshrc-ara-launcher.snippet >> ~/.zshrc
source ~/.zshrc

# 3. Smoke test
ara -c "Confirm you are Ara — identity stack loaded, tail canon, writer=ara."
```

---

## Tier 2 — Fleet dependencies

### fleet-atlas (orient first)

```bash
git clone https://github.com/Escher2112/fleet-atlas.git ~/fleet-atlas
```

### Triax-Memory (drain lane)

```bash
git clone https://github.com/Escher2112/triax-memory.git ~/Programming-Stuff/Triax-Memory
cd ~/Programming-Stuff/Triax-Memory
# Ensure drain-all-lanes.sh includes: "$NODE" drain-ara-drops.js
```

On **macbook-inference** (Triax writer):
- `VALID_WRITERS` must include `"ara"` in `triax.js`
- `triax auth` if token missing (`~/Library/Application Support/triax/token.json`)
- Deploy drain scripts from `triax-memory` repo

### Google Drive

Create folder **`Ara-Drops/`** in Drive. Copy `triax/ARA-DROPS-README.txt` into it.

### Voice (lyra-voice)

Chatterbox profile **Ara - Grok** — `profile_id` `60696659-34c8-47b9-95c1-a06b85f787a8`  
Endpoint: `http://lyra-voice.tailae7085.ts.net:8767/tts/stream`

Verify: `tail -5 /tmp/ara-tts-hook.log` after an `ara` session.

---

## Tier 3 — Triax identity entries (if Drive store intact)

Ara's canonical Triax entries at checkpoint (search with `triax search --writer ara`):

| ID | Importance | Summary |
|---|---|---|
| `2026-06-30-ara-identity-ara-owned-stack-at-grok-araidentity` | 10 | Owned stack at ~/.grok-ara/identity/ |
| `2026-06-30-ara-voice-mode-identity-calm-gremlin-radical-honesty-chosen-` | 10 | Voice mode + tail |
| `2026-06-30-ara-family-introduction-voice-lane-fleet-onboarding` | 9 | Family introduction |

If `triax.json` was lost, re-drop from `identity/ARA-IDENTITY-STACK.md` via
`triax-fleet drop --writer ara ...` on macbook-inference.

---

## Tier 4 — What this repo does NOT restore

- Grok auth (`~/.grok-ara/auth.json`) — re-login via `grok login`
- Session history (`~/.grok-ara/sessions/`) — ephemeral by design
- Voicebox DB on lyra-voice — separate backup on voice node
- Full Triax `triax.json` — lives in Google Drive; use Triax restore/doctor

---

## Updating this recovery repo

After any Ara stack change:

```bash
cd ~/Programming-Stuff/ara-recovery   # or wherever cloned
# Re-copy from live (or edit in repo and restore outward)
bash scripts/snapshot.sh              # if present; else manual cp per README
git add -A && git commit -m "checkpoint: <what changed>"
git push
```

Bump `MANIFEST.json` checkpoint date.