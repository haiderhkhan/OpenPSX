"""Provider-agnostic model configuration for all PSX War Room specialists."""

from __future__ import annotations

import os

from agents import ModelSettings, OpenAIChatCompletionsModel, set_tracing_disabled
from agents.model_settings import Reasoning
from dotenv import load_dotenv
from openai import AsyncOpenAI


load_dotenv()

GEMINI_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
DEFAULT_OPENAI_MODEL = "gpt-5.6"
DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"

LOW_TOKEN_MODEL_SETTINGS = ModelSettings(
    temperature=0,
    max_tokens=180,
    reasoning=Reasoning(effort="minimal"),
)


def get_model_provider() -> str:
    """Return a validated provider selection from ``MODEL_PROVIDER``."""

    provider = os.getenv("MODEL_PROVIDER", "openai").strip().lower()
    if provider not in {"openai", "gemini"}:
        raise ValueError(
            "MODEL_PROVIDER must be either 'openai' or 'gemini', "
            f"not {provider!r}."
        )
    return provider


# Gemini's OpenAI-compatible endpoint does not support OpenAI trace export.
# Explicitly re-enable tracing for OpenAI in case another import disabled it.
set_tracing_disabled(get_model_provider() != "openai")


def get_specialist_model() -> str | OpenAIChatCompletionsModel:
    """Return the configured specialist model for ``MODEL_PROVIDER``."""

    provider = get_model_provider()
    if provider == "openai":
        return os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL).strip() or DEFAULT_OPENAI_MODEL

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("MODEL_PROVIDER=gemini requires GEMINI_API_KEY in the environment.")
    model_name = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip()
    return OpenAIChatCompletionsModel(
        model=model_name or DEFAULT_GEMINI_MODEL,
        openai_client=AsyncOpenAI(
            api_key=api_key,
            base_url=GEMINI_OPENAI_BASE_URL,
        ),
    )