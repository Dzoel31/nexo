"""LLM conversation payload contracts."""

from pydantic import BaseModel, Field


class LLMMessagePayload(BaseModel):
    """Standard message payload sent to an LLM."""

    role: str = Field(description="Role string recognized by the LLM API")
    content: str = Field(description="Prompt or response text")


class ConversationContext(BaseModel):
    """Previous summary and active messages supplied to an LLM."""

    summary: str | None = Field(
        default=None, description="Rolling conversation summary"
    )
    messages: list[LLMMessagePayload] = Field(
        default_factory=list, description="Recent messages within the token budget"
    )
