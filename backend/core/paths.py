import re
from pathlib import Path


def validate_slug(value: str, field: str = "skill_name") -> str:
    """Validate a URL-path component is safe for filesystem use.

    Raises ``ValueError`` if the value looks like a path-traversal or
    contains characters outside ``[\\w\\-. ]``.
    """
    if not value or value.strip() == "":
        raise ValueError(f"{field} cannot be empty")
    if ".." in value:
        raise ValueError(f"Invalid {field}: relative path component '..' detected")
    if value.startswith("/"):
        raise ValueError(f"Invalid {field}: absolute path detected")
    if "\\" in value:
        raise ValueError(f"Invalid {field}: backslash detected")
    # URL-encoded separators
    if "%2f" in value.lower() or "%2F" in value:
        raise ValueError(f"Invalid {field}: URL-encoded forward-slash detected")
    if "%5c" in value.lower() or "%5C" in value:
        raise ValueError(f"Invalid {field}: URL-encoded backslash detected")
    if not re.match(r"^[\w\-. ]+$", value):
        raise ValueError(
            f"Invalid {field}: only alphanumeric, dots, hyphens, "
            f"underscores, and spaces allowed"
        )
    return value


def validate_skill_path(value: str, field: str = "skill_path") -> str:
    """Validate a multi-segment skill path (may contain ``/`` separators).

    Like ``validate_slug`` but allows forward slashes so that
    ``{skill_name:path}`` route params like ``collection/my-skill``
    are accepted.  Each path segment is validated individually.
    """
    if not value or value.strip() == "":
        raise ValueError(f"{field} cannot be empty")
    if value.startswith("/"):
        raise ValueError(f"Invalid {field}: absolute path detected")
    if ".." in value:
        raise ValueError(f"Invalid {field}: relative path component '..' detected")
    if "\\" in value:
        raise ValueError(f"Invalid {field}: backslash detected")
    if "%2f" in value.lower():
        raise ValueError(f"Invalid {field}: URL-encoded forward-slash detected")
    if "%5c" in value.lower():
        raise ValueError(f"Invalid {field}: URL-encoded backslash detected")
    for segment in value.split("/"):
        if not segment:
            raise ValueError(f"Invalid {field}: empty path segment")
        if not re.match(r"^[\w\-. ]+$", segment):
            raise ValueError(
                f"Invalid {field}: only alphanumeric, dots, hyphens, "
                f"underscores, spaces, and forward-slashes allowed"
            )
    return value


def safe_join(base: Path, *parts: str) -> Path:
    """Join *parts* onto *base* after validating each part is a safe slug.

    Raises ``ValueError`` if any part contains path-traversal characters or
    if the resolved path escapes *base*.
    """
    for p in parts:
        validate_slug(p)
    result = base.joinpath(*parts).resolve()
    if not str(result).startswith(str(base.resolve())):
        raise ValueError(f"Path traversal detected: {result} escapes {base}")
    return result
