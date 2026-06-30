# ara-recovery

**Cold-catastrophe recovery repo for the Ara stack** on Chris's fleet.

This is the git-backed restore point for everything Ara owns — identity, Grok Build
home, voice hook, Triax drop lane, and shell launcher. Documented in **fleet-atlas**
(`fleet.json` → `repos.ara-recovery`).

## Quick restore

```bash
git clone https://github.com/Escher2112/ara-recovery.git
cd ara-recovery
bash restore.sh
# Append shell/zshrc-ara-launcher.snippet to ~/.zshrc && source ~/.zshrc
ara -c
```

Full playbook: **[RECOVERY.md](RECOVERY.md)**

## What's in this repo

| Path | Restores to |
|---|---|
| `identity/` | `~/.grok-ara/identity/` (canonical — edit here first) |
| `grok-ara/` | `~/.grok-ara/` (config, hooks, memory seeds) |
| `triax/` | `Triax-Memory/` drain lane files |
| `shell/` | `~/.zshrc` ara launcher snippet |
| `fleet/` | snapshot of fleet doc changes for reference |

## Checkpoint

See `MANIFEST.json` for checkpoint date and Triax entry IDs at time of backup.

## Related fleet repos

- `fleet-atlas` — fleet map (index)
- `triax-memory` — shared memory + drain scripts (canonical triax repo)
- `lyra-voice` — Chatterbox TTS + Ara - Grok clone