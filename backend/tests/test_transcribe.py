"""P7-03 POST /api/transcribe with a mocked httpx: success, too large, bad type, flag off, upstream failure."""
from __future__ import annotations

import httpx
import pytest

from backend import config
from backend.voice import transcribe as voice

AUDIO = ("blob", b"\x1aE\xdf\xa3 fake webm bytes", "audio/webm;codecs=opus")  # what Chrome's MediaRecorder sends


@pytest.fixture(autouse=True)
def env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "FEATURE_VOICE", True)
    monkeypatch.setattr(config, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(config, "GROQ_WHISPER_MODEL", "whisper-large-v3-turbo")


class FakePost:
    def __init__(self, monkeypatch: pytest.MonkeyPatch, outcome) -> None:
        self.calls: list[dict] = []
        self.outcome = outcome
        monkeypatch.setattr(voice.httpx, "post", self)

    def __call__(self, url, *, headers, data, files, timeout):
        self.calls.append({"url": url, "headers": headers, "data": data, "files": files})
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return httpx.Response(self.outcome[0], json=self.outcome[1], request=httpx.Request("POST", url))


def post(client, audio=AUDIO):
    return client.post("/api/transcribe", files={"audio": audio})


def test_success_returns_text_and_duration(client, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakePost(monkeypatch, (200, {"text": " How has OGDC done this year? ", "duration": 2.4}))
    res = post(client)
    assert res.status_code == 200 and res.json() == {"text": "How has OGDC done this year?", "duration_s": 2.4}
    (call,) = fake.calls
    assert call["url"] == voice.GROQ_URL and call["headers"]["Authorization"] == "Bearer test-key"
    assert call["data"] == {"model": "whisper-large-v3-turbo", "language": "en", "response_format": "verbose_json"}
    assert call["files"]["file"][0] == "speech.webm"  # type from the content type: Chrome's filename is "blob"


def test_too_large_is_400(client, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakePost(monkeypatch, (200, {"text": "x"}))
    res = post(client, ("big.webm", b"0" * (voice.MAX_BYTES + 1), "audio/webm"))
    assert res.status_code == 400 and "10 MB" in res.json()["error"]["message"] and fake.calls == []


@pytest.mark.parametrize("audio", [("notes.txt", b"hello", "text/plain"), ("clip.flac", b"fLaC", "application/octet-stream")])
def test_bad_type_is_400(client, monkeypatch: pytest.MonkeyPatch, audio) -> None:
    fake = FakePost(monkeypatch, (200, {"text": "x"}))
    res = post(client, audio)
    assert res.status_code == 400 and res.json()["error"]["code"] == "BAD_REQUEST" and fake.calls == []


def test_flag_off_is_feature_off(client, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "FEATURE_VOICE", False)
    res = post(client)
    assert res.status_code == 403 and res.json()["error"]["code"] == "FEATURE_OFF"


@pytest.mark.parametrize("outcome", [(500, {"error": "boom"}), (429, {"error": "rate"}), httpx.ConnectError("down")])
def test_upstream_failure_is_503(client, monkeypatch: pytest.MonkeyPatch, outcome) -> None:
    FakePost(monkeypatch, outcome)
    res = post(client)
    assert res.status_code == 503 and res.json()["error"]["code"] == "UPSTREAM"


def test_missing_key_is_503_without_a_call(client, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakePost(monkeypatch, (200, {"text": "x"}))
    monkeypatch.setattr(config, "GROQ_API_KEY", "")
    assert post(client).status_code == 503 and fake.calls == []


def test_extension_is_used_when_the_content_type_is_generic() -> None:
    assert voice.audio_kind("application/octet-stream", "memo.m4a") == "m4a"
    assert voice.audio_kind("audio/ogg; codecs=opus", "blob") == "ogg"
    assert voice.audio_kind(None, "blob") is None


@pytest.mark.parametrize(("flag", "key", "shown"), [(True, "test-key", True), (True, "", False), (False, "test-key", False)])
def test_health_shows_the_mic_only_with_the_flag_and_a_key(client, monkeypatch, flag: bool, key: str, shown: bool) -> None:
    monkeypatch.setattr(config, "FEATURE_VOICE", flag)
    monkeypatch.setattr(config, "GROQ_API_KEY", key)
    assert client.get("/api/health").json()["features"]["voice"] is shown
