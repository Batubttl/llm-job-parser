# LLM Job Parser

![CI](https://github.com/Batubttl/llm-job-parser/actions/workflows/ci.yml/badge.svg)

A small FastAPI service that turns raw job postings into validated, structured JSON using a local LLM.

Paste a messy job posting, get back clean data:

```json
{
  "job": {
    "title": "Werkstudent AI Infrastructure",
    "company": "ArtiQuare",
    "location": "München",
    "skills": ["Python", "FastAPI", "Docker"],
    "remote": true,
    "employment_type": "werkstudent"
  },
  "model": "ollama_chat/qwen2.5:7b"
}
```

## Why

I built this as a learning project to get hands-on experience with FastAPI, Pydantic, LiteLLM and Docker. It focuses on a common real-world LLM task: turning unstructured text into data that other systems can rely on. LLM output is never trusted blindly; every response is validated against a strict schema before it leaves the service.

## Architecture

```
Client ──► FastAPI ──► LiteLLM ──► Ollama (local LLM)
              │                         │
              └──── Pydantic validation ◄┘
```

1. **FastAPI** receives the request and validates the input (length limits, types).
2. **LiteLLM** sends the text to the model with a system prompt that includes the JSON schema generated from the Pydantic model.
3. The model's answer is validated with **Pydantic**. If it does not match the schema, the API returns `502 Bad Gateway` instead of passing on bad data.

## Tech stack

- **Python 3.14**, **FastAPI**, **Pydantic v2**
- **LiteLLM** as a provider-agnostic LLM client
- **Ollama** running `qwen2.5:7b` locally
- **pytest** with a mocked LLM, **ruff** for linting and formatting, **mypy** in strict mode
- **Docker** and **GitHub Actions** for CI

## API

| Method | Endpoint | Body | Description |
|---|---|---|---|
| `GET` | `/health` | – | Liveness check |
| `POST` | `/parse` | JSON: `{"text": "..."}` | Parse a job posting sent as JSON |
| `POST` | `/parse/text` | Plain text | Parse a job posting pasted as-is, including line breaks |

Interactive docs are available at `http://127.0.0.1:8000/docs` once the service is running.

**Status codes:** `200` success · `422` invalid input (for example, text shorter than 20 characters) · `502` the LLM returned data that did not match the schema.

## Getting started

### Prerequisites

- [Ollama](https://ollama.com) with the model pulled:
  ```bash
  ollama pull qwen2.5:7b
  ```
- Python 3.14 (for local development) or Docker

### Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Run with Docker

```bash
docker build -t llm-job-parser .
docker run --rm -p 8000:8000 \
  -e LLM_API_BASE=http://host.docker.internal:11434 \
  llm-job-parser
```

On Linux, also add `--add-host=host.docker.internal:host-gateway` to the `docker run` command.

### Try it

```bash
curl -X POST http://127.0.0.1:8000/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "ArtiQuare is hiring a Werkstudent AI Infrastructure in Munich. Python, FastAPI and Docker required."}'
```

Or send a multi-line posting from a file:

```bash
curl -X POST http://127.0.0.1:8000/parse/text \
  -H "Content-Type: text/plain" \
  --data-binary @job_posting.txt
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `LLM_MODEL` | `ollama_chat/qwen2.5:7b` | Any model identifier supported by LiteLLM |
| `LLM_API_BASE` | `http://localhost:11434` | Base URL of the LLM server |

Because the service talks to the model through LiteLLM, switching to a hosted provider should only require changing these variables (I have only tested it with Ollama).

## Development

```bash
pytest -v          # 9 tests, the LLM is mocked so no model is needed
ruff check .       # lint
ruff format .      # format
mypy app tests     # strict type checking
```

GitHub Actions runs linting, type checking, the tests and a Docker build on every push.

## Design decisions

- **One schema, two jobs.** The `JobPosting` Pydantic model validates the LLM output *and* generates the JSON schema used in the prompt, so the two can never drift apart.
- **Separate error codes.** `422` means the client sent bad input; `502` means the upstream model misbehaved. This makes failures easy to diagnose.
- **Mocked LLM in tests.** Tests are fast, deterministic and run in CI without a GPU or Ollama. They check how the code handles valid JSON, wrong types and non-JSON answers.
- **Ollama runs on the host, not in Docker.** Docker on macOS cannot use the Apple Silicon GPU, so the container reaches Ollama on the host via `host.docker.internal`.
- **Configuration through environment variables**, so the same image runs locally and in Docker without code changes.
- **Docker image details:** dependencies are installed before the code is copied (faster rebuilds thanks to layer caching), and the app runs as a non-root user.

## Limitations and possible next steps

- No automatic retry when the model returns invalid output
- Requests are handled synchronously; an async LLM client would scale better
- No authentication or rate limiting
- Extraction quality has only been checked manually on a handful of postings; a small labelled evaluation set would make this measurable

## Project structure

```
app/
  main.py       # FastAPI app and endpoints
  llm.py        # LiteLLM call and output validation
  schemas.py    # Pydantic models
tests/
  test_api.py   # API tests with a mocked parser
  test_llm.py   # LLM layer tests with a mocked litellm.completion
Dockerfile
pyproject.toml  # pytest, ruff and mypy configuration
```