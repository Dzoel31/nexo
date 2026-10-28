"""Legacy compatibility facade. Do not add new logic here."""

from db.models import MessageRole
from db.repositories.competition import (
    create_competition,
    delete_competition,
    get_competition_by_id,
    list_active_competitions,
    update_competition_reminders,
)
from db.repositories.conversation import (
    CONVERSATION_TTL,
    get_or_create_conversation,
    reset_all_conversation_history,
    reset_conversation_history,
)
from db.repositories.scheduled_announcement import (
    cancel_scheduled_announcement,
    create_scheduled_announcement,
    get_due_scheduled_announcements,
    list_pending_announcements,
    mark_announcement_status,
)
from db.repositories.token_usage import (
    get_guild_token_leaderboard,
    get_user_token_stats,
    log_token_usage,
)
from services.llm.context import (
    check_and_trigger_rolling_summary,
    get_conversation_context,
    save_message,
)
from services.llm.token_counter import (
    BASE_OVERHEAD_TOKENS,
    COMPACTION_THRESHOLD,
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL_NAME,
    MAX_COMPLETION_TOKENS,
    TARGET_RETAIN_TOKENS,
    TOOL_BUFFER_TOKENS,
    TOTAL_CONTEXT_WINDOW,
    USABLE_HISTORY_BUDGET,
    ai_client,
    count_token,
)

__all__ = [
    "BASE_OVERHEAD_TOKENS",
    "COMPACTION_THRESHOLD",
    "CONVERSATION_TTL",
    "LLM_API_KEY",
    "LLM_BASE_URL",
    "LLM_MODEL_NAME",
    "MAX_COMPLETION_TOKENS",
    "TARGET_RETAIN_TOKENS",
    "TOOL_BUFFER_TOKENS",
    "TOTAL_CONTEXT_WINDOW",
    "USABLE_HISTORY_BUDGET",
    "MessageRole",
    "ai_client",
    "cancel_scheduled_announcement",
    "check_and_trigger_rolling_summary",
    "count_token",
    "create_competition",
    "create_scheduled_announcement",
    "delete_competition",
    "get_competition_by_id",
    "get_conversation_context",
    "get_due_scheduled_announcements",
    "get_guild_token_leaderboard",
    "get_or_create_conversation",
    "get_user_token_stats",
    "list_active_competitions",
    "list_pending_announcements",
    "log_token_usage",
    "mark_announcement_status",
    "reset_all_conversation_history",
    "reset_conversation_history",
    "save_message",
    "update_competition_reminders",
]
