from unittest.mock import MagicMock
import discord
from utils.auth_helper import get_member_from_context, has_role, has_permission


class DummyRole:
    def __init__(self, role_id: int, name: str):
        self.id = role_id
        self.name = name


class DummyPermissions:
    def __init__(self, **kwargs):
        self.administrator = kwargs.get("administrator", False)
        self.manage_events = kwargs.get("manage_events", False)
        self.manage_messages = kwargs.get("manage_messages", False)
        self.create_public_threads = kwargs.get("create_public_threads", False)
        self.send_messages = kwargs.get("send_messages", True)


class DummyMember:
    def __init__(self, user_id: int, roles=None, perms=None, is_owner=False):
        self.id = user_id
        self.roles = roles or []
        self.guild_permissions = perms or DummyPermissions()
        self.guild = MagicMock()
        self.guild.owner_id = user_id if is_owner else 999999999


def test_get_member_from_context():
    # 1. None
    assert get_member_from_context(None) is None

    # 2. Member directly
    member = DummyMember(123)
    assert get_member_from_context(member) == member

    # 3. From discord.Message
    msg = MagicMock(spec=discord.Message)
    msg.author = member
    assert get_member_from_context(msg) == member

    # 4. From discord.Interaction
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = member
    assert get_member_from_context(interaction) == member


def test_has_role():
    role_leader = DummyRole(1468847955745181757, "Leader")
    role_member = DummyRole(1479423491513122897, "Member")

    member = DummyMember(123, roles=[role_leader, role_member])

    assert has_role(member, "Leader") is True
    assert has_role(member, "Secretary") is False
    assert has_role(member, "NonExistentRole") is False


def test_has_permission_admin_and_owner():
    # Server Owner
    owner_member = DummyMember(123, is_owner=True)
    msg_owner = MagicMock()
    msg_owner.author = owner_member
    assert has_permission(msg_owner, "manage_events") is True

    # Administrator
    admin_member = DummyMember(456, perms=DummyPermissions(administrator=True))
    msg_admin = MagicMock()
    msg_admin.author = admin_member
    assert has_permission(msg_admin, "manage_events") is True


def test_has_permission_native_and_roles():
    # User with native manage_events permission
    event_manager = DummyMember(789, perms=DummyPermissions(manage_events=True))
    msg_event = MagicMock()
    msg_event.author = event_manager
    assert has_permission(msg_event, "manage_events") is True

    # User without native permission but with allowed role
    role_core = DummyRole(1492049177876893836, "Staff-Core")
    core_member = DummyMember(101, roles=[role_core])
    msg_core = MagicMock()
    msg_core.author = core_member
    assert (
        has_permission(msg_core, "manage_events", allowed_roles=["Staff-Core"]) is True
    )
    assert has_permission(msg_core, "manage_events", allowed_roles=["Leader"]) is False

    # Plain member without permission or allowed role
    role_plain = DummyRole(1479423491513122897, "Member")
    plain_member = DummyMember(202, roles=[role_plain])
    msg_plain = MagicMock()
    msg_plain.author = plain_member
    assert (
        has_permission(
            msg_plain, "manage_events", allowed_roles=["Leader", "Co-Leader"]
        )
        is False
    )
