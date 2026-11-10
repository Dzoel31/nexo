"""Ensure legacy import facades preserve object identity."""

import importlib

import db.schemas as db_schemas
import schemas.discord as discord_schemas
import utils.schemas as legacy_discord
import utils.webhook_schemas as legacy_webhooks


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


def test_discord_schema_facade_exports_are_identical():
    modules = {name: "schemas.discord" for name in discord_schemas.__all__}
    modules["get_clean_schema"] = "utils.schema_utils"
    _assert_exports_are_identical(legacy_discord, modules)


def test_webhook_schema_facade_exports_are_identical():
    modules = {name: "schemas.github.webhooks" for name in legacy_webhooks.__all__}
    _assert_exports_are_identical(legacy_webhooks, modules)
