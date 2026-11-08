"""FastAPI application exposing the job posting parser."""

from fastapi import FastAPI, HTTPException, status

from app.llm import MODEL, LLMOutputError, parse_job_posting
from app.schemas import ParseRequest, ParseResponse

app = FastAPI(
    title="LLM Job Parser",
    description="Turns raw job posting text into validated, structured JSON using a local LLM.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Simple liveness check, useful for Docker and monitoring."""
    return {"status": "ok"}


@app.post("/parse", response_model=ParseResponse)
def parse(request: ParseRequest) -> ParseResponse:
    """Extract structured data from a raw job posting."""
    try:
        job = parse_job_posting(request.text)
    except LLMOutputError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The language model returned data that did not match the expected schema.",
        ) from exc
    return ParseResponse(job=job, model=MODEL)