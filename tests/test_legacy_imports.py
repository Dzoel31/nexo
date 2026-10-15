"""Ensure legacy import facades preserve object identity."""

import importlib

import db.schemas as db_schemas
import schemas.discord as discord_schemas
import utils.schemas as legacy_discord
import utils.webhook_schemas as legacy_webhooks
from db import repository


def _assert_exports_are_identical(facade, module_by_name):
    for name in facade.__all__:
        module = importlib.import_module(module_by_name.get(name, facade.__name__))
        assert getattr(facade, name) is getattr(module, name), name


def test_database_schema_facade_exports_are_identical():
    modules = {
        "CompetitionCreate": "db.schemas.competition",
        "CompetitionRead": "db.schemas.competition",
        "ConversationRead": "db.schemas.conversation",
        "MessageRole": "db.models",
        "MessageCreate": "db.schemas.conversation",
        "MessageRead": "db.schemas.conversation",
        "ScheduledAnnouncementCreate": "db.schemas.scheduled_announcement",
        "ScheduledAnnouncementRead": "db.schemas.scheduled_announcement",
        "ScheduledEventCreate": "db.schemas.scheduled_event",
        "ScheduledEventRead": "db.schemas.scheduled_event",
        "TokenUsageLogCreate": "db.schemas.token_usage",
        "TokenUsageLogRead": "db.schemas.token_usage",
        "UserTokenStats": "db.schemas.token_usage",
        "GuildTokenLeaderboardItem": "db.schemas.token_usage",
        "ConversationContext": "schemas.llm.conversation",
        "LLMMessagePayload": "schemas.llm.conversation",
    }
    _assert_exports_are_identical(db_schemas, modules)


def test_repository_facade_exports_are_identical():
    modules = {
        "get_or_create_conversation": "db.repositories.conversation",
        "save_message": "services.llm.context",
        "get_conversation_context": "services.llm.context",
        "check_and_trigger_rolling_summary": "services.llm.context",
        "reset_conversation_history": "db.repositories.conversation",
        "log_token_usage": "db.repositories.token_usage",
        "get_user_token_stats": "db.repositories.token_usage",
        "get_guild_token_leaderboard": "db.repositories.token_usage",
        "create_scheduled_announcement": "db.repositories.scheduled_announcement",
        "get_due_scheduled_announcements": "db.repositories.scheduled_announcement",
        "mark_announcement_status": "db.repositories.scheduled_announcement",
        "list_pending_announcements": "db.repositories.scheduled_announcement",
        "cancel_scheduled_announcement": "db.repositories.scheduled_announcement",
        "create_competition": "db.repositories.competition",
        "list_active_competitions": "db.repositories.competition",
        "get_competition_by_id": "db.repositories.competition",
        "delete_competition": "db.repositories.competition",
        "update_competition_reminders": "db.repositories.competition",
        "count_token": "services.llm.token_counter",
    }
    _assert_exports_are_identical(repository, modules)


def test_discord_schema_facade_exports_are_identical():
    modules = {name: "schemas.discord" for name in discord_schemas.__all__}
    modules["get_clean_schema"] = "utils.schema_utils"
    _assert_exports_are_identical(legacy_discord, modules)


def test_webhook_schema_facade_exports_are_identical():
    modules = {name: "schemas.github.webhooks" for name in legacy_webhooks.__all__}
    _assert_exports_are_identical(legacy_webhooks, modules)
