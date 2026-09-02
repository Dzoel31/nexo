import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import discord

logger = logging.getLogger("auth_helper")

ROLES_CONFIG_PATH = Path("config/roles.json")
_ROLES_CACHE: Dict[str, int] = {}
_ROLES_CACHE_MTIME: float = 0.0


def load_roles_config() -> Dict[str, int]:
    """Loads and caches role ID mappings from config/roles.json."""
    global _ROLES_CACHE, _ROLES_CACHE_MTIME
    if not ROLES_CONFIG_PATH.exists():
        return {}

    try:
        current_mtime = ROLES_CONFIG_PATH.stat().st_mtime
        if current_mtime != _ROLES_CACHE_MTIME:
            with open(ROLES_CONFIG_PATH, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                parsed: Dict[str, int] = {}
                if isinstance(raw_data, dict):
                    for name, role_id_str in raw_data.items():
                        if str(role_id_str).strip().isdigit():
                            parsed[name.strip()] = int(str(role_id_str).strip())
                _ROLES_CACHE = parsed
                _ROLES_CACHE_MTIME = current_mtime
                logger.info(f"Loaded {len(_ROLES_CACHE)} roles from config/roles.json")
        return _ROLES_CACHE
    except Exception as e:
        logger.warning(f"Failed to load roles from config/roles.json: {e}")
        return _ROLES_CACHE


def get_member_from_context(ctx_obj: Any) -> Optional[discord.Member]:
    """
    Safely extracts a discord.Member object from either discord.Interaction,
    discord.Message, commands.Context, or custom member objects.
    """
    if ctx_obj is None:
        return None

    # 1. Message or Context with author
    if hasattr(ctx_obj, "author") and ctx_obj.author is not None:
        author = ctx_obj.author
        if hasattr(author, "guild_permissions") and hasattr(author, "roles"):
            return author
        guild = getattr(ctx_obj, "guild", None)
        if guild and hasattr(guild, "get_member") and hasattr(author, "id"):
            member = guild.get_member(author.id)
            if member:
                return member
        return author

    # 2. Interaction with user
    if hasattr(ctx_obj, "user") and ctx_obj.user is not None:
        user = ctx_obj.user
        if hasattr(user, "guild_permissions") and hasattr(user, "roles"):
            return user
        guild = getattr(ctx_obj, "guild", None)
        if guild and hasattr(guild, "get_member") and hasattr(user, "id"):
            member = guild.get_member(user.id)
            if member:
                return member
        return user

    # 3. Direct Member object
    if hasattr(ctx_obj, "guild_permissions") and hasattr(ctx_obj, "roles"):
        return ctx_obj

    return None


def has_role(member: Any, *role_names: str) -> bool:
    """Checks if a member has any of the specified roles by name or configured ID."""
    if not member or not role_names or not hasattr(member, "roles"):
        return False

    roles_map = load_roles_config()
    target_role_ids = {roles_map[name] for name in role_names if name in roles_map}
    target_role_names = {name.lower() for name in role_names}

    roles_list = member.roles
    if callable(roles_list):
        roles_list = roles_list()

    for r in roles_list:
        r_id = getattr(r, "id", None)
        r_name = getattr(r, "name", "")
        if r_id in target_role_ids or (
            r_name and str(r_name).lower() in target_role_names
        ):
            return True

    return False


def has_permission(
    ctx_obj: Any,
    permission_name: str,
    allowed_roles: Optional[List[str]] = None,
) -> bool:
    """
    Comprehensive authorization check:
    1. Returns True if member is Server Owner or Administrator.
    2. Returns True if member has the specified native Discord permission.
    3. Returns True if member has any role listed in allowed_roles.
    """
    member = get_member_from_context(ctx_obj)
    if not member:
        return False

    guild = getattr(member, "guild", None)
    if not guild:
        return False

    # Server Owner bypass
    owner_id = getattr(guild, "owner_id", None)
    member_id = getattr(member, "id", None)
    if owner_id is not None and member_id is not None and member_id == owner_id:
        return True

    perms = getattr(member, "guild_permissions", None)
    if perms:
        if getattr(perms, "administrator", False) is True:
            return True
        if getattr(perms, permission_name, False) is True:
            return True

    # Check Role Whitelist Fallback
    if allowed_roles and has_role(member, *allowed_roles):
        return True

    return False
