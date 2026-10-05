# What Now?

A local-first AI next-action coach for college students.

Built for the [Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01).

## The problem

Students know what matters. The hard part is deciding what to start after a long day. Existing productivity apps add decisions; this one removes them.

## What it does

You give it:
- Your energy level (1–5)
- How many minutes you have
- Your task list (with deadlines and energy cost)

It returns **one action** — with a reason, a 2-minute first step, a timebox, and a fallback.

## Stack

- **Model:** Gemma 3 4B, running locally via [Ollama](https://ollama.com)
- **Backend:** FastAPI + HTMX
- **Storage:** SQLite
- **Everything local.** No cloud, no API keys, no data leaves your machine.

## Run it

1. Install Ollama: https://ollama.com/download
2. Pull the model: `ollama pull gemma3:4b`
3. Start Ollama: `ollama serve`
4. In this repo:
`uv sync
uv run uvicorn src.what_now.main:app --reload`
5. Open `http://127.0.0.1:8000`, Swap models with an env var
`WHATNOW_MODEL=qwen2.5:7b uv run uvicorn src.what_now.main:app`

## Why local

The task list holds exam deadlines, internship applications, personal goals. None of it needs to leave the laptop.
