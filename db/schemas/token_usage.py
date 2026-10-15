from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TokenUsageLogCreate(BaseModel):
    """Skema input pencatatan log konsumsi token LLM."""

    guild_id: int | None = None
    user_id: int
    username: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0


class TokenUsageLogRead(BaseModel):
    """Skema representasi data log konsumsi token dari database."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    guild_id: int | None
    user_id: int
    username: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: int
    created_at: datetime


class UserTokenStats(BaseModel):
    """Skema agregasi statistik pemakaian token seorang pengguna."""

    user_id: int
    username: str
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    interactions: int
    avg_tokens_per_interaction: float


class GuildTokenLeaderboardItem(BaseModel):
    """Skema item pemakaian token pengguna pada leaderboard server."""

    user_id: int
    username: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    interactions: int
