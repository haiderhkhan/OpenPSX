"""Chat + voice endpoints 12–13 (SCHEMA.md §4.2): /chat since P7-02, /transcribe (Groq Whisper) since P7-03."""
from __future__ import annotations

import logging

from fastapi import APIRouter, File, UploadFile

from backend import config
from backend.api import ApiException
from backend.routing import chat_answer
from backend.schemas.chat import ChatAnswer, ChatRequest, Transcription
from backend.voice import transcribe as voice

log = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


@router.post("/chat")
def chat(body: ChatRequest) -> ChatAnswer:
    """One question, one answer: no history is kept or sent (P7). LLM failures become TEMPLATE, never 500."""
    if not config.DB_PATH.exists():
        raise ApiException(503, "UPSTREAM", "Market database not built yet (run scripts/build_db.py).")
    try:
        return chat_answer.answer(body.question)
    except ApiException:
        raise
    except Exception as exc:  # the composer absorbs LLM failures; anything left is an upstream fault, not a 500
        log.exception("chat answer failed")
        raise ApiException(503, "UPSTREAM", "The answer could not be composed right now. Please try again.") from exc


@router.post("/transcribe")
def transcribe(audio: UploadFile = File(...)) -> Transcription:
    """Multipart `audio` (webm/ogg/wav/mp3/m4a, ≤ 10 MB) → text. Flag off → 403; Groq failure → 503."""
    data = audio.file.read(voice.MAX_BYTES + 1)  # one byte over the cap is enough to reject it
    return voice.transcribe(data, audio.content_type, audio.filename)
