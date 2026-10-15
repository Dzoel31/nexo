from pydantic import BaseModel, Field


class GetServerChannelsSchema(BaseModel):
    pass


class GetServerRolesSchema(BaseModel):
    pass


class CheckVoiceChannelSchema(BaseModel):
    channel_name: str | None = Field(
        default=None,
        description="Voice channel name (omit for current/active user channel)",
    )
