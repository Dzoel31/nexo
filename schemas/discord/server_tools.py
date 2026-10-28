from pydantic import BaseModel, Field


class GetServerChannelsSchema(BaseModel):
    pass


class GetServerRolesSchema(BaseModel):
    pass


class FindServerMembersSchema(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=100,
        description="Username, display name, global name, or nickname to search for",
    )


class NotifyMemberSchema(BaseModel):
    member_id: int = Field(description="Discord ID of the exact member to notify")
    message: str = Field(
        min_length=1,
        max_length=1900,
        description="Message to send to the selected member",
    )


class CheckVoiceChannelSchema(BaseModel):
    channel_name: str | None = Field(
        default=None,
        description="Voice channel name (omit for current/active user channel)",
    )
