"""API tests. The LLM is mocked, so these run without Ollama."""

import pytest
from fastapi.testclient import TestClient

from app import main
from app.llm import LLMOutputError
from app.schemas import JobPosting

client = TestClient(main.app)

SAMPLE_TEXT = (
    "ArtiQuare is hiring a Werkstudent AI Infrastructure in Munich. Python and Docker are required."
)


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_parse_returns_structured_job(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_parse(text: str) -> JobPosting:
        return JobPosting(
            title="Werkstudent AI Infrastructure",
            company="ArtiQuare",
            skills=["Python", "Docker"],
        )

    monkeypatch.setattr(main, "parse_job_posting", fake_parse)

    response = client.post("/parse", json={"text": SAMPLE_TEXT})

    assert response.status_code == 200
    body = response.json()
    assert body["job"]["company"] == "ArtiQuare"
    assert body["job"]["skills"] == ["Python", "Docker"]


def test_parse_rejects_too_short_text() -> None:
    response = client.post("/parse", json={"text": "too short"})

    assert response.status_code == 422


def test_parse_returns_502_when_llm_output_is_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def broken_parse(text: str) -> JobPosting:
        raise LLMOutputError("LLM returned garbage")

    monkeypatch.setattr(main, "parse_job_posting", broken_parse)

    response = client.post("/parse", json={"text": SAMPLE_TEXT})

    assert response.status_code == 502


def test_parse_text_accepts_multiline_plain_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    received: list[str] = []

    def fake_parse(text: str) -> JobPosting:
        received.append(text)
        return JobPosting(title="Werkstudent GenAI")

    monkeypatch.setattr(main, "parse_job_posting", fake_parse)
    multiline = "Werkstudent GenAI (m/w/d)\n\nYour tasks:\n- Build LLM pipelines\n- Python"

    response = client.post(
        "/parse/text",
        content=multiline,
        headers={"Content-Type": "text/plain"},
    )

    assert response.status_code == 200
    assert response.json()["job"]["title"] == "Werkstudent GenAI"
    assert received == [multiline]


def test_parse_text_rejects_too_short_text() -> None:
    response = client.post(
        "/parse/text",
        content="too short",
        headers={"Content-Type": "text/plain"},
    )

    assert response.status_code == 422
