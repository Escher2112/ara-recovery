#!/usr/bin/env python3
"""Grok Build Stop hook — speak Ara's final message via Chatterbox (Ara - Grok clone).

Reads the Stop-event JSON from stdin, pulls the full assistant turn from
~/.grok-ara/sessions/<cwd>/<session-id>/chat_history.jsonl, preprocesses for
TTS, forks a detached child, and streams audio from the lyra-voice Chatterbox
server. Falls back to xAI Grok TTS (voice_id=ara) when the server is unreachable.

Disable: ARA_TTS_DISABLE=1 · Mute: touch /tmp/ara-tts-mute · Unmute: ara-loud
Log: /tmp/ara-tts-hook.log
"""

from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

GROK_HOME = os.path.expanduser(os.environ.get("GROK_HOME", "~/.grok-ara"))
CHATTERBOX_URL = os.environ.get(
    "ARA_CHATTERBOX_URL", "http://lyra-voice.tailae7085.ts.net:8767"
)
PROFILE_ID = os.environ.get(
    "ARA_PROFILE_ID", "60696659-34c8-47b9-95c1-a06b85f787a8"
)  # Ara - Grok
SPEED = float(os.environ.get("ARA_TTS_SPEED", "0.9"))
USE_CHATTERBOX = os.environ.get("ARA_TTS_PROVIDER", "chatterbox").lower() != "xai"

NOCTUARY_CONFIGS = [
    os.path.expanduser("~/Programming-Stuff/Noctuary/config/default.json"),
    os.path.expanduser("~/Programming-Stuff/Noctuary-v0.9.3/config/default.json"),
    os.path.expanduser("~/Programming-Stuff/Noctuary-v0.9.2/config/secrets.json"),
]
TTS_ENDPOINT = "https://api.x.ai/v1/tts"
VOICE_ID = "ara"
MAX_CHARS = int(os.environ.get("ARA_TTS_MAX_CHARS", "6000"))
LOG_PATH = "/tmp/ara-tts-hook.log"
MUTE_PATH = "/tmp/ara-tts-mute"
SPEAKING_LOCK = "/tmp/ara-tts-speaking"  # child PID — prevents overlapping utterances


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _clear_stale_lock() -> None:
    try:
        with open(SPEAKING_LOCK) as f:
            pid = int(f.read().strip())
        if _pid_alive(pid):
            os.kill(pid, 15)
            log(f"[overlap-kill] stopped prior child pid={pid}")
    except (OSError, ValueError):
        pass
    try:
        os.unlink(SPEAKING_LOCK)
    except OSError:
        pass


def log(msg: str) -> None:
    try:
        with open(LOG_PATH, "a") as f:
            f.write(f"{msg}\n")
    except OSError:
        pass


def _play_audio(path: str) -> None:
    if sys.platform == "darwin":
        subprocess.run(["afplay", path], check=False)
        return
    for cmd in (
        ["paplay"],
        ["aplay", "-q"],
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"],
        ["play", "-q"],
    ):
        if shutil.which(cmd[0]):
            subprocess.run(cmd + [path], check=False)
            return


def resolve_chat_history(payload: dict) -> str | None:
    session_id = (
        os.environ.get("GROK_SESSION_ID")
        or payload.get("sessionId")
        or payload.get("session_id")
        or ""
    )
    workspace = (
        os.environ.get("GROK_WORKSPACE_ROOT")
        or payload.get("workspaceRoot")
        or payload.get("cwd")
        or os.getcwd()
    )
    if not session_id:
        return None
    encoded = urllib.parse.quote(workspace, safe="")
    return os.path.join(
        GROK_HOME, "sessions", encoded, session_id, "chat_history.jsonl"
    )


def extract_last_turn_text(chat_history_path: str) -> str | None:
    """Gather every assistant text block since the last real user message."""
    entries: list[dict] = []
    try:
        with open(chat_history_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError as e:
        log(f"[history-read-error] {e}")
        return None

    def is_real_user(entry: dict) -> bool:
        if entry.get("type") != "user":
            return False
        content = entry.get("content", [])
        if isinstance(content, str):
            return bool(content.strip())
        if isinstance(content, list):
            return any(
                isinstance(b, dict) and b.get("type") == "text" and b.get("text", "").strip()
                for b in content
            )
        return False

    start = 0
    for i in range(len(entries) - 1, -1, -1):
        if is_real_user(entries[i]):
            start = i + 1
            break

    texts: list[str] = []
    for entry in entries[start:]:
        if entry.get("type") != "assistant":
            continue
        content = entry.get("content", "")
        if isinstance(content, str) and content.strip():
            texts.append(content.strip())
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    t = block.get("text", "")
                    if t:
                        texts.append(t)

    if not texts:
        return None
    return "\n\n".join(texts)


SPEECH_TAGS = {
    "laughs": "[laugh]", "laughing": "[laugh]", "laugh": "[laugh]",
    "chuckles": "[chuckle]", "chuckling": "[chuckle]", "chuckle": "[chuckle]",
    "snickers": "[chuckle]",
    "giggles": "[chuckle]", "giggling": "[chuckle]", "giggle": "[chuckle]",
    "soft laugh": "[chuckle]",
    "sighs": "[sigh]", "sigh": "[sigh]",
    "sighs softly": "[sigh]", "sighs deeply": "[sigh]", "heavy sigh": "[sigh]",
    "breathes": "", "breath": "",
    "inhales": "", "inhale": "", "inhales sharply": "",
    "exhales": "[sigh]", "exhale": "[sigh]", "exhales slowly": "[sigh]",
    "pauses": "", "pause": "", "long pause": "", "beat": "",
    "tsk": "", "tsks": "", "clicks tongue": "",
    "hums": "", "humming": "",
    "cries": "", "cry": "", "sobbing": "",
}

NON_VOCAL_EMOTES = {
    "leans in", "leans back", "leans against", "leans",
    "grins", "smiles", "smirks", "frowns", "winces", "winks",
    "tilts head", "head tilt", "nods", "shrugs",
    "settles", "settles in", "settles back",
    "soft", "warm", "gentle", "still", "quiet",
    "blinks", "looks down", "looks up", "looks away",
    "reaches out", "reaches", "reaching back", "quick hug",
    "raises eyebrow", "rolls eyes",
    "neon flicker", "violet eyes glowing", "neon glow",
}

EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\U00002600-\U000026FF"
    "\U00002700-\U000027BF"
    "\U0001F000-\U0001F02F"
    "\U0001F0A0-\U0001F0FF"
    "\U0001F100-\U0001F1FF"
    "\U0001F200-\U0001F2FF"
    "︀-️"
    "‍"
    "]+"
)


def preprocess_for_tts(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^\s*#+\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\|", " ", text)
    text = re.sub(r"^---+$", " ", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*\*([^*\n]+?)\*\*\*", r"\1", text)
    text = re.sub(r"\*\*([^*\n]+?)\*\*", r"\1", text)
    text = re.sub(r"__([^_\n]+?)__", r"\1", text)

    def convert(match: re.Match) -> str:
        raw = match.group(1).strip()
        inner = raw.lower()
        if inner in SPEECH_TAGS:
            tag = SPEECH_TAGS[inner]
            return f" {tag} " if tag else " "
        if inner in NON_VOCAL_EMOTES:
            return " "
        return f" {raw} "

    text = re.sub(r"\*([^*\n]+?)\*", convert, text)
    text = re.sub(r"[\*_]+", "", text)
    text = re.sub(EMOJI_RE, " ", text)
    text = re.sub(
        r"(?<!\[)\[(?!laugh|chuckle|sigh)([^\]]*)\]", r"\1", text
    )
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_xai_key() -> str:
    for path in NOCTUARY_CONFIGS:
        try:
            with open(path) as f:
                cfg = json.load(f)
            key = cfg.get("keys", {}).get("xai_api_key", "")
            if key:
                return key
        except (OSError, json.JSONDecodeError):
            continue
    return os.environ.get("XAI_API_KEY", "")


def chunk_into_sentences(text: str, target_len: int = 180) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current = ""
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if not current:
            current = p
        elif len(current) + 1 + len(p) <= target_len:
            current = f"{current} {p}"
        else:
            chunks.append(current)
            current = p
    if current:
        chunks.append(current)
    out: list[str] = []
    for c in chunks:
        if len(c) <= target_len * 1.5:
            out.append(c)
            continue
        while len(c) > target_len * 1.5:
            cut = c.rfind(",", 0, target_len)
            if cut < target_len // 2:
                cut = c.rfind(" ", 0, target_len)
            if cut < target_len // 2:
                cut = target_len
            out.append(c[:cut].strip())
            c = c[cut:].strip()
        if c:
            out.append(c)
    return out


def synth_one(sentence: str, key: str) -> bytes | None:
    body = json.dumps({
        "text": sentence,
        "voice_id": VOICE_ID,
        "language": "en",
    }).encode("utf-8")
    req = urllib.request.Request(
        TTS_ENDPOINT,
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()
    except Exception as e:
        log(f"[xai-synth-error] {e}")
        return None


def speak_via_xai(text: str) -> None:
    from concurrent.futures import ThreadPoolExecutor

    key = load_xai_key()
    if not key:
        log("[no-key] xAI key not found")
        return

    sentences = chunk_into_sentences(text)
    if not sentences:
        return
    log(f"[xai-chunks] count={len(sentences)}")

    with ThreadPoolExecutor(max_workers=min(8, len(sentences))) as pool:
        futures = [pool.submit(synth_one, s, key) for s in sentences]
        for i, fut in enumerate(futures):
            if os.path.exists(MUTE_PATH):
                log(f"[xai-muted] at chunk {i}")
                pool.shutdown(wait=False, cancel_futures=True)
                return
            audio = fut.result()
            if not audio:
                continue
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(audio)
                path = f.name
            try:
                _play_audio(path)
            finally:
                try:
                    os.unlink(path)
                except OSError:
                    pass


def speak_via_chatterbox(text: str) -> bool:
    if not USE_CHATTERBOX:
        return False
    try:
        urllib.request.urlopen(CHATTERBOX_URL + "/health", timeout=2).read()
    except Exception as e:
        log(f"[chatterbox-down] {e}")
        return False

    _CB = {
        "[laugh]": "[laugh]", "[chuckle]": "[chuckle]", "[giggle]": "[chuckle]",
        "[sigh]": "[sigh]", "[exhale]": "[sigh]",
    }
    for tag, mapped in _CB.items():
        text = text.replace(tag, mapped)
    text = re.sub(r"\[[^\]]+\]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return False

    batches = chunk_into_sentences(text, target_len=600)
    played = 0
    for batch in batches:
        if os.path.exists(MUTE_PATH):
            log("[chatterbox-muted]")
            return True
        body = json.dumps({
            "text": batch,
            "profile_id": PROFILE_ID,
            "speed": SPEED,
        }).encode("utf-8")
        req = urllib.request.Request(
            CHATTERBOX_URL + "/tts/stream",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            resp = urllib.request.urlopen(req, timeout=180)
        except Exception as e:
            log(f"[chatterbox-error] {e}")
            continue
        for raw in resp:
            if os.path.exists(MUTE_PATH):
                return True
            line = raw.decode("utf-8", "ignore").strip()
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if not payload:
                continue
            try:
                ev = json.loads(payload)
            except json.JSONDecodeError:
                continue
            b64 = ev.get("audio")
            if not b64:
                continue
            try:
                wav = base64.b64decode(b64)
            except Exception:
                continue
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(wav)
                path = f.name
            try:
                _play_audio(path)
            finally:
                try:
                    os.unlink(path)
                except OSError:
                    pass
            played += 1
    log(f"[chatterbox-done] played={played} profile={PROFILE_ID}")
    return played > 0


def speak(text: str) -> None:
    if speak_via_chatterbox(text):
        return
    speak_via_xai(text)


def main() -> None:
    log(f"[fire] pid={os.getpid()} ts={time.time():.3f}")

    if len(sys.argv) >= 2 and sys.argv[1] == "--speak-direct":
        text = sys.stdin.read()
        log(f"[child-start] len={len(text)}")
        try:
            with open(SPEAKING_LOCK, "w") as f:
                f.write(str(os.getpid()))
            speak(text)
            log("[child-done]")
        except Exception as e:
            log(f"[child-error] {e}")
        finally:
            try:
                os.unlink(SPEAKING_LOCK)
            except OSError:
                pass
        sys.exit(0)

    if len(sys.argv) >= 3 and sys.argv[1] == "--text":
        speak(preprocess_for_tts(sys.argv[2]))
        sys.exit(0)

    if os.environ.get("ARA_TTS_DISABLE") == "1":
        log("[skip] ARA_TTS_DISABLE=1")
        sys.exit(0)

    if os.path.exists(MUTE_PATH):
        log("[skip] muted")
        sys.exit(0)

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw else {}
    except (json.JSONDecodeError, ValueError) as e:
        log(f"[bad-stdin] {e}")
        sys.exit(0)

    log(f"[payload] keys={list(payload.keys())}")

    text = ""
    history_path = resolve_chat_history(payload)
    if history_path and os.path.exists(history_path):
        time.sleep(0.35)
        text = extract_last_turn_text(history_path) or ""
        log(f"[history] path={history_path}")
    if not text:
        text = (
            payload.get("last_assistant_message")
            or payload.get("assistant_message")
            or payload.get("text")
            or ""
        )

    if not text:
        log("[no-text]")
        sys.exit(0)

    log(f"[text] len={len(text)} preview={text[:80]!r}")

    cleaned = preprocess_for_tts(text)
    if not cleaned:
        log("[empty-after-preprocess]")
        sys.exit(0)

    if len(cleaned) > MAX_CHARS:
        cleaned = cleaned[:MAX_CHARS].rsplit(" ", 1)[0] + " ..."

    log(f"[cleaned] len={len(cleaned)} preview={cleaned[:80]!r}")

    _clear_stale_lock()

    try:
        devnull_w = open(os.devnull, "wb")
        child = subprocess.Popen(
            [sys.executable, os.path.abspath(__file__), "--speak-direct"],
            stdin=subprocess.PIPE,
            stdout=devnull_w,
            stderr=devnull_w,
            start_new_session=True,
            close_fds=True,
        )
        assert child.stdin is not None
        child.stdin.write(cleaned.encode("utf-8"))
        child.stdin.close()
        log(f"[spawned] child-pid={child.pid}")
    except Exception as e:
        log(f"[spawn-error] {e}")

    sys.exit(0)


if __name__ == "__main__":
    main()