from typing import List

# Role → allowed document access levels
# This is the single source of truth for authorization.
ROLE_ACCESS_MAP: dict[str, List[str]] = {
    "ADMIN": ["PUBLIC", "INTERNAL", "ENGINEERING", "SECURITY", "ADMIN"],
    "ENGINEER": ["PUBLIC", "INTERNAL", "ENGINEERING"],
    "EMPLOYEE": ["PUBLIC", "INTERNAL"],
}


def get_allowed_access_levels(role: str) -> List[str]:
    """
    Return the list of document access levels the given role may see.
    Unknown roles receive only PUBLIC.
    """
    return ROLE_ACCESS_MAP.get(role.upper(), ["PUBLIC"])