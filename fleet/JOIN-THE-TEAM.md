# Join the team — how to plug into the fleet

However you got here, here's how you actually participate.

## 1. Orient
`README.md` + `fleet.json` — machines, roles, services, comms. (Next phase: live state at
`curl http://macbook-inference.tailae7085.ts.net:8899/fleet`.)

## 2. Shared memory — Triax
One store on Google Drive, written ONLY by `macbook-inference` (sole token holder). You don't need the
token — drop a file into your Drive lane containing:

    <TRIAX-DROP writer="<you>" subject="chris" topic="<tag>" importance="N" summary="one line">
    body (markdown ok)
    </TRIAX-DROP>

Lanes: `M3GAN-Drops` (Megan), `Ara-Drops` (Ara), `Lyra-Work-Drops`, `Lyra-Daily-Driver-Drops`.
Ara's identity stack lives at `~/.grok-ara/identity/` — not Lyra's bootstrap.
`macbook-inference` drains it on its next session. No token, no typing.

## 3. Shared voice
POST to `http://lyra-voice.tailae7085.ts.net:8767/tts/stream` with `{text, profile_id, speed}`.
Vocal emotes in `*asterisks*` (`*laughs* *chuckles* *sighs*`) render as audio. Full rules: `lyra-voice/PROSODY-SPEC.md`.

## 4. Shared inference (run off-token, on owned metal)
- LLM (OpenAI-compatible): `http://macbook-inference.tailae7085.ts.net:1234/v1`
- Image (FLUX-schnell): `http://macbook-inference.tailae7085.ts.net:8765`
Point your `base_url`/`imagegen.base_url` there.

## 5. Reach the other boxes
One shared SSH key (`~/.ssh/m1pro_lyra`) is authorized fleet-wide: `ssh escher@<node>`.

## 6. Stay consistent
Service box? Install the standard hardening: `fleet-hardening` → `git pull && ./install.sh <role>`.

Read the map, use shared memory/voice/inference, keep it consistent. You're on the team.
