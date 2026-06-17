import re

WEBCAM_URL_PATTERN = re.compile(r"^webcam://(\d+)$", re.IGNORECASE)

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
    if WEBCAM_URL_PATTERN.match(normalized):
        return normalized.lower()
    if not RTSP_URL_PATTERN.match(normalized):
        raise ValueError(
            "Invalid stream URL. Use rtsp://..., rtsps://..., or webcam://0 for a local camera"
        )
    return normalized


def is_webcam_url(value: str) -> bool:
    return bool(WEBCAM_URL_PATTERN.match(value.strip()))
