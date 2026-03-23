# Bot Development Plan

## Overview

This document outlines the development plan for building a Telegram bot that integrates with the LMS backend. The bot allows users to check system health, browse labs and scores, and ask questions in plain language using an LLM for intent routing.

## Task 1: Plan and Scaffold

We create the project skeleton with a testable handler architecture. Handlers are pure functions that take input and return text — they don't know about Telegram. This separation of concerns allows us to test handlers via `--test` mode without connecting to Telegram. The entry point (`bot.py`) routes commands to handlers and supports both test mode and Telegram mode.

**Key decisions:**
- Handlers in `bot/handlers/` are plain async functions
- `--test` mode calls handlers directly, prints to stdout
- Config loaded from `.env.bot.secret` using `python-dotenv`
- Dependencies managed with `uv` and `pyproject.toml`

## Task 2: Backend Integration

We implement real API calls to the LMS backend. The `/health` handler will make an HTTP request to check if the backend is up. The `/labs` handler fetches available labs. The `/scores` handler retrieves pass rates for a specific lab.

**Key decisions:**
- API client in `bot/services/lms_client.py`
- Bearer token authentication from `LMS_API_KEY`
- Error handling: backend down produces friendly messages, not crashes
- All URLs and keys from environment variables

## Task 3: Intent-Based Natural Language Routing

We add LLM-powered intent routing. Users can ask questions in plain language ("What labs are available?", "Show me task 2 scores"). The LLM analyzes the input and decides which tool (API call) to invoke.

**Key decisions:**
- LLM client in `bot/services/llm_client.py`
- Each backend endpoint exposed as an LLM tool with clear descriptions
- Tool descriptions are critical — the LLM reads them to decide what to call
- Intent router in `bot/handlers/intent_router.py`

## Task 4: Containerize and Deploy

We containerize the bot with a Dockerfile and add it as a service in `docker-compose.yml`. The bot runs alongside the backend on the VM.

**Key decisions:**
- Multi-stage Dockerfile for small image
- Docker networking: containers use service names, not `localhost`
- Environment variables passed via `.env.docker.secret`
- README documents deployment steps

## Architecture Summary

```
User → Telegram → bot.py → handlers → services → LMS Backend / LLM
                ↓
           --test mode (direct handler calls)
```

This architecture keeps business logic (handlers) separate from transport (Telegram), making the code testable and maintainable.
