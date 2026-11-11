"""LLM client: turns raw job posting text into a validated JobPosting."""

import json
import os

import litellm
from pydantic import ValidationError

from app.schemas import JobPosting

# Read settings from environment variables, with local defaults.
# Later, Docker will override LLM_API_BASE to reach Ollama on the host.
MODEL = os.getenv("LLM_MODEL", "ollama_chat/qwen2.5:7b")
API_BASE = os.getenv("LLM_API_BASE", "http://localhost:11434")

SYSTEM_PROMPT = (
    "You extract structured data from job postings. "
    "Respond with a single JSON object that matches this JSON schema:\n"
    f"{json.dumps(JobPosting.model_json_schema())}\n"
    "Use null for unknown values. Do not invent information. "
    "Return only JSON, no explanations."
)


class LLMOutputError(Exception):
    """Raised when the LLM response does not match the JobPosting schema."""


def parse_job_posting(text: str) -> JobPosting:
    """Send the job posting to the LLM and validate the JSON it returns."""
    response = litellm.completion(
        model=MODEL,
        api_base=API_BASE,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    content = response.choices[0].message.content or ""

    try:
        return JobPosting.model_validate_json(content)
    except ValidationError as exc:
        raise LLMOutputError(f"LLM returned invalid data: {exc}") from exc
