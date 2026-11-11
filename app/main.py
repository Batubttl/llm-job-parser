"""FastAPI application exposing the job posting parser."""

from typing import Annotated

from fastapi import Body, FastAPI, HTTPException, status

from app.llm import MODEL, LLMOutputError, parse_job_posting
from app.schemas import MAX_TEXT_LENGTH, MIN_TEXT_LENGTH, ParseRequest, ParseResponse

app = FastAPI(
    title="LLM Job Parser",
    description="Turns raw job posting text into validated, structured JSON using a local LLM.",
    version="0.2.0",
)


def _parse_or_502(text: str) -> ParseResponse:
    """Run the parser and translate invalid LLM output into HTTP 502."""
    try:
        job = parse_job_posting(text)
    except LLMOutputError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The language model returned data that did not match the expected schema.",
        ) from exc
    return ParseResponse(job=job, model=MODEL)


@app.get("/health")
def health() -> dict[str, str]:
    """Simple liveness check, useful for Docker and monitoring."""
    return {"status": "ok"}


@app.post("/parse", response_model=ParseResponse)
def parse(request: ParseRequest) -> ParseResponse:
    """Extract structured data from a job posting sent as JSON."""
    return _parse_or_502(request.text)


@app.post("/parse/text", response_model=ParseResponse)
def parse_text(
    text: Annotated[
        str,
        Body(
            media_type="text/plain",
            min_length=MIN_TEXT_LENGTH,
            max_length=MAX_TEXT_LENGTH,
        ),
    ],
) -> ParseResponse:
    """Extract structured data from a job posting sent as plain text.

    Convenient for pasting multi-line postings without JSON escaping.
    """
    return _parse_or_502(text)