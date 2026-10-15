"""Voice → text through Groq Whisper (P7-03, R-04 §4). Audio is posted once and never stored."""
from __future__ import annotations

import logging

import httpx

from backend import config
from backend.api import ApiException
from backend.schemas.chat import Transcription

log = logging.getLogger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
MAX_BYTES = 10 * 1024 * 1024
TIMEOUT_S = 30.0
# Base content type (parameters such as ";codecs=opus" dropped) or file extension → the upload's extension.
CONTENT_TYPES = {
    "audio/webm": "webm", "video/webm": "webm", "audio/ogg": "ogg", "audio/wav": "wav", "audio/x-wav": "wav",
    "audio/wave": "wav", "audio/mpeg": "mp3", "audio/mp3": "mp3", "audio/mp4": "m4a", "audio/x-m4a": "m4a",
    "audio/m4a": "m4a",
}
EXTENSIONS = frozenset({"webm", "ogg", "wav", "mp3", "m4a"})


def audio_kind(content_type: str | None, filename: str | None) -> str | None:
    """The extension to send, or None for a type we don't accept."""
    base = (content_type or "").split(";")[0].strip().lower()
    if base in CONTENT_TYPES:
        return CONTENT_TYPES[base]
    ext = (filename or "").rsplit(".", 1)[-1].lower() if "." in (filename or "") else ""
    return ext if ext in EXTENSIONS else None


def transcribe(data: bytes, content_type: str | None, filename: str | None) -> Transcription:
    if not config.FEATURE_VOICE:
        raise ApiException(403, "FEATURE_OFF", "Voice input is switched off.")
    kind = audio_kind(content_type, filename)
    if kind is None:
        raise ApiException(400, "BAD_REQUEST", "Unsupported audio type: send webm, ogg, wav, mp3 or m4a.")
    if not data:
        raise ApiException(400, "BAD_REQUEST", "The audio file is empty.")
    if len(data) > MAX_BYTES:
        raise ApiException(400, "BAD_REQUEST", "The audio file is larger than 10 MB.")
    if not config.GROQ_API_KEY:
        raise ApiException(503, "UPSTREAM", "Voice transcription is not configured. Please type your question.")
    try:
        resp = httpx.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
            data={"model": config.GROQ_WHISPER_MODEL, "language": "en", "response_format": "verbose_json"},
            files={"file": (f"speech.{kind}", data, (content_type or "").split(";")[0] or f"audio/{kind}")},
            timeout=TIMEOUT_S,
        )
        resp.raise_for_status()
        body = resp.json()
    except Exception as exc:  # status error, network error, non-JSON reply: an upstream failure is 503, never 500
        status = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else type(exc).__name__
        log.warning("groq transcription failed: %s", status)
        raise ApiException(503, "UPSTREAM", "Voice transcription is unavailable right now. Please type your question.") from exc
    duration = body.get("duration")
    return Transcription(text=str(body.get("text") or "").strip(),
                         duration_s=float(duration) if isinstance(duration, (int, float)) else None)
