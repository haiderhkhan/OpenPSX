"""Chat + voice endpoints 12–13 (SCHEMA.md §4.2). P0-04 stubs; owned by Track B from P7."""
from __future__ import annotations

from fastapi import APIRouter, File, UploadFile

from backend.api import load_fixture
from backend.schemas.chat import ChatAnswer, ChatRequest, Transcription

router = APIRouter(tags=["chat"])


@router.post("/chat")
def chat(body: ChatRequest) -> ChatAnswer:
    return load_fixture("chat.json", ChatAnswer)


@router.post("/transcribe")
def transcribe(audio: UploadFile = File(...)) -> Transcription:
    return load_fixture("transcribe.json", Transcription)
