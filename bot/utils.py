import re

def has_role(member, role_name):
    """
    Check if a member has a specific role.
    """
    return any(role.name == role_name for role in member.roles)

def remove_prefix(map_name):
    prefixes_to_remove = ["TrCTF-", "TrCTFBlitz-", "TrArena-"]
    for prefix in prefixes_to_remove:
        map_name = map_name.replace(prefix, "")
    map_name = re.sub(r"([a-zA-Z0-9])([A-Z0-9])", r"\1 \2", map_name)
    return map_name
