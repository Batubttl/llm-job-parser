"""Tests for the LLM layer. litellm.completion is mocked."""

from collections.abc import Callable
from types import SimpleNamespace
from typing import Any

import litellm
import pytest

from app import llm


def fake_completion(content: str) -> Callable[..., SimpleNamespace]:
    """Build a fake litellm.completion that always returns `content`."""

    def _completion(**kwargs: Any) -> SimpleNamespace:
        message = SimpleNamespace(content=content)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    return _completion


def test_valid_llm_json_is_parsed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        litellm,
        "completion",
        fake_completion('{"title": "Data Engineer", "skills": ["SQL"]}'),
    )

    job = llm.parse_job_posting("some job posting text")

    assert job.title == "Data Engineer"
    assert job.skills == ["SQL"]
    assert job.company is None


def test_llm_json_with_wrong_types_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        litellm,
        "completion",
        fake_completion('{"title": "Data Engineer", "skills": "SQL"}'),
    )

    with pytest.raises(llm.LLMOutputError):
        llm.parse_job_posting("some job posting text")


def test_llm_non_json_output_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        litellm,
        "completion",
        fake_completion("Sure! Here is the job posting as JSON..."),
    )

    with pytest.raises(llm.LLMOutputError):
        llm.parse_job_posting("some job posting text")
