# src/what_now/agent.py
"""Calls the local Ollama server to generate one next action."""

import json
import os

import httpx

from .prompts import SYSTEM_PROMPT, build_user_prompt

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL = os.getenv("WHATNOW_MODEL", "gemma3:4b")
TIMEOUT_SECONDS = 30.0

REQUIRED_FIELDS = {"action", "why", "first_step", "timebox_minutes", "fallback"}


class AgentError(Exception):
    """Raised when the agent cannot produce a valid action."""


async def get_next_action(context: dict) -> dict:
    """Ask Ollama for one next action. Returns a dict matching the schema."""
    payload = {
        "model": MODEL,
        "system": SYSTEM_PROMPT,
        "prompt": build_user_prompt(context),
        "stream": False,
        "format": "json",          # Ollama constrains output to valid JSON
        "options": {
            "temperature": 0.4,     # low = deterministic, less creative drift
            "top_p": 0.9,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
    except httpx.ConnectError as exc:
        raise AgentError("Ollama is not running. Start it with `ollama serve`.") from exc
    except httpx.TimeoutException as exc:
        raise AgentError("Ollama took too long to respond. Try again.") from exc
    except httpx.HTTPStatusError as exc:
        raise AgentError(f"Ollama returned an error: {exc.response.status_code}") from exc

    raw = response.json().get("response", "").strip()
    if not raw:
        raise AgentError("Model returned an empty response.")

    try:
        action = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AgentError(f"Model returned invalid JSON: {raw[:200]}") from exc

    missing = REQUIRED_FIELDS - action.keys()
    if missing:
        raise AgentError(f"Model response missing fields: {sorted(missing)}")

    return action