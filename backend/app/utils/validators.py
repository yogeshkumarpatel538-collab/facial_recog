import re

RTSP_URL_PATTERN = re.compile(
    r"^rtsps?://"
    r"(?:[^:@/]+(?::[^@/]*)?@)?"
    r"(?:\[[^\]]+\]|[^:/]+)"
    r"(?::\d+)?"
    r"(?:/[^\s]*)?$",
    re.IGNORECASE,
)


def validate_password_strength(value: str) -> str:
    if not any(char.isupper() for char in value):
        raise ValueError("Password must contain at least one uppercase letter")
    if not any(char.islower() for char in value):
        raise ValueError("Password must contain at least one lowercase letter")
    if not any(char.isdigit() for char in value):
        raise ValueError("Password must contain at least one digit")
    return value


def validate_rtsp_url(value: str) -> str:
    normalized = value.strip()
    if not RTSP_URL_PATTERN.match(normalized):
        raise ValueError(
            "Invalid RTSP URL. Must start with rtsp:// or rtsps:// and include a valid host"
        )
    return normalized
