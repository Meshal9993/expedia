"""Hotel RAG DTOs. Models contain no provider or database access."""

from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class HotelChatRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    question: str = Field(strict=True, min_length=1, max_length=4000)
    conversation_id: UUID | None = None

    @field_validator("question")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Question must not be blank")
        return value.strip()


class StayContext(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    check_in: date
    check_out: date
    rooms: int = Field(default=1, strict=True, ge=1, le=1000)

    @model_validator(mode="after")
    def bounded_stay(self):
        if not 1 <= (self.check_out - self.check_in).days <= 31:
            raise ValueError("A stay must contain 1–31 nights")
        return self


class SqlProposal(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    sql: str = Field(strict=True, min_length=1, max_length=8000)
    parameters: list[str | int | float | None] = Field(max_length=64)
    stay: StayContext | None = None

    @field_validator("parameters", mode="before")
    @classmethod
    def scalar_parameters(cls, values):
        import math
        if not isinstance(values, list) or any(
            type(value) not in (str, int, float, type(None))
            or (type(value) is int and not -(2**63) <= value < 2**63)
            or (isinstance(value, str) and len(value) > 4000)
            or (isinstance(value, float) and not math.isfinite(value))
            for value in values
        ):
            raise ValueError("Parameters must be bounded JSON scalars")
        return values


class HotelRetrieval(BaseModel):
    model_config = ConfigDict(frozen=True)
    executed_sql: str
    records: list[dict]
    truncated: bool = False


class StayAssessment(BaseModel):
    model_config = ConfigDict(frozen=True)
    hotel_id: str
    required_dates: list[str]
    missing_dates: list[str]
    total_rate_cents: int | None = None
    enough_rooms: bool | None = None


class HotelChatResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    conversation_id: UUID
    question: str
    proposed_sql: str
    executed_sql: str
    parameters: list[str | int | float | None]
    retrieved_records: list[dict]
    answer: str
    state: Literal["answer", "no_matches", "insufficient_data"]
    truncated: bool = False
    stay_assessments: list[StayAssessment] = Field(default_factory=list)
    simulated_data: bool = True


class ChatPromptMetadata(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    prompt_hash: str
    prompt_version: str


class ChatEventWrite(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    conversation_id: UUID
    turn_id: UUID
    stage: Literal["user", "proposed_sql", "executed_sql", "retrieval_result",
                   "retrieval_error", "model_error", "assistant"]
    content: dict


class ChatConversation(BaseModel):
    model_config = ConfigDict(frozen=True)
    conversation_id: UUID
    created_at: str
    updated_at: str
    prompt_hash: str
    prompt_version: str


class ChatHistoryEvent(BaseModel):
    model_config = ConfigDict(frozen=True)
    event_id: int
    conversation_id: UUID
    turn_id: UUID
    timestamp: str
    stage: Literal["user", "proposed_sql", "executed_sql", "retrieval_result",
                   "retrieval_error", "model_error", "assistant"]
    content: dict


class ChatHistory(BaseModel):
    model_config = ConfigDict(frozen=True)
    conversation: ChatConversation
    events: list[ChatHistoryEvent]
    truncated: bool = False
