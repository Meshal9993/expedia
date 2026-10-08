"""The chat HTTP contract; no configuration or provider access in models."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ChatMessage(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(strict=True, min_length=1, max_length=24000)

    @field_validator("content")
    @classmethod
    def nonblank_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message must not be blank")
        return value

    @model_validator(mode="after")
    def bounded_question(self):
        if self.role == "user" and len(self.content) > 4000:
            raise ValueError("Question is too long")
        return self


class ChatRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    messages: list[ChatMessage] = Field(min_length=1, max_length=21)

    @model_validator(mode="after")
    def valid_conversation(self):
        if any(message.role != ("user" if i % 2 == 0 else "assistant")
               for i, message in enumerate(self.messages)) or self.messages[-1].role != "user":
            raise ValueError("Messages must alternate from user and end with user")
        if sum(len(message.content) for message in self.messages) > 24000:
            raise ValueError("Conversation is too long; start a new chat")
        return self


class ChatEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: Literal["delta", "done", "error"]
    text: str = ""
    code: Literal["configuration", "limited", "timeout", "unavailable", "incomplete"] | None = None
