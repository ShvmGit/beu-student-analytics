# BEU Result Intelligence Assistant

A multi-agent AI system that fetches, analyzes, and explains Bihar Engineering University (BEU) exam results using LLMs via Groq.

## Quick Start

```bash
# 1. Clone and enter directory
cd beu-result-ai

# 2. Create virtual environment
py -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# 5. Run the CLI
py app/cli.py
```

## Architecture

```
User → Chat Agent (A) → Fetch Agent (B) → BEU API
                                              ↓
       Chat Agent (A) ← Analysis Agent (C) ← Normalized Result
```

- **Agent A (Chat)**: Manages conversation, collects input, explains results
- **Agent B (Fetch)**: Calls BEU API, validates, normalizes (no LLM)
- **Agent C (Analysis)**: Computes metrics, generates insights via LLM

## API Endpoints (FastAPI)

```bash
# Start the server
uvicorn app.main:app --reload

# Analyze a result
POST /result/analyze
Body: {"reg_no": "24153125054", "semester": 2}

# Health check
GET /result/health
```

## Tests

```bash
pytest tests/ -v
```

## Environment Variables

| Variable | Required | Default |
|----------|----------|---------|
| `GROQ_API_KEY` | ✅ Yes | — |
| `BEU_API_BASE_URL` | No | `https://beu-bih.ac.in/backend/v1` |
| `LOG_LEVEL` | No | `INFO` |
| `CACHE_TTL_SECONDS` | No | `3600` |
