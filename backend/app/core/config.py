from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "People Counting System"
    app_env: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    host: str = "0.0.0.0"
    port: int = 8000

    database_url: str = "sqlite:///./people_counting.db"

    secret_key: str = "change-me-to-a-random-secret-key"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    jwt_algorithm: str = "HS256"

    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # AI Worker
    worker_enabled: bool = True
    worker_poll_interval_seconds: int = 30
    worker_yolo_model: str = "yolo11n.pt"
    worker_confidence_threshold: float = 0.5
    worker_iou_threshold: float = 0.5
    worker_line_y_ratio: float = 0.5
    worker_frame_skip: int = 2
    worker_reconnect_delay_seconds: int = 5
    worker_max_reconnect_attempts: int = 0  # 0 = unlimited
    worker_db_write_interval_seconds: float = 0.0  # 0 = write immediately
    worker_tracker_config: str = "bytetrack.yaml"
    worker_person_class_id: int = 0
    worker_rtsp_transport: str = "tcp"

    # Redis / Real-time
    redis_enabled: bool = True
    redis_url: str = "redis://localhost:6379/0"
    redis_live_counts_channel: str = "live_counts"
    redis_reconnect_delay_seconds: float = 3.0
    redis_max_reconnect_attempts: int = 0

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if value.startswith("["):
                import json

                return json.loads(value)
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
