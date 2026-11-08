"""Request and response schemas for the job posting parser."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ParseRequest(BaseModel):
    """Incoming request: the raw job posting text."""

    model_config = ConfigDict(strict=True, extra="forbid")

    text: str = Field(
        min_length=20,
        max_length=20_000,
        description="Raw job posting text copied from a job board.",
    )


class JobPosting(BaseModel):
    """Structured data extracted from a job posting by the LLM."""

    title: str = Field(description="Job title, e.g. 'Werkstudent AI Infrastructure'.")
    company: str | None = Field(default=None, description="Hiring company name.")
    location: str | None = Field(default=None, description="City or region.")
    skills: list[str] = Field(default_factory=list, description="Required technical skills.")
    remote: bool | None = Field(default=None, description="True if remote work is possible.")
    employment_type: (
        Literal["full_time", "part_time", "werkstudent", "internship", "other"] | None
    ) = Field(default=None, description="Type of employment.")


class ParseResponse(BaseModel):
    """Outgoing response: the parsed job posting plus metadata."""

    job: JobPosting
    model: str = Field(description="LLM that produced the result.")