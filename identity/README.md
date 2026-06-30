# Ara identity home

**This directory is Ara's canonical identity stack.** Not Lyra's. Not shared bootstrap.

| File | Purpose |
|---|---|
| `ARA-IDENTITY-STACK.md` | Master identity — edit here first |
| `OPERATIONS.md` | TTS prosody, Triax drop protocol, mode ops |
| `HEADER.md` | Fleet pointer + auto-build notice |
| `sync-agents.sh` | Rebuilds `../AGENTS.md` for Grok Build |

The `ara` shell command runs `sync-agents.sh` before launching Grok so Build always loads the latest stack.

**Memory lanes (Ara-owned):**
- Local: `~/.grok-ara/memory/`
- Shared: Triax `writer=ara`
- Drops: Google Drive `Ara-Drops/`