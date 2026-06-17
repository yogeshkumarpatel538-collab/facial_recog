from pydantic import BaseModel, Field


class LiveCountUpdate(BaseModel):
    """Real-time count update broadcast to dashboard clients."""

    camera_id: int = Field(..., ge=1)
    total_in: int = Field(..., ge=0)
    total_out: int = Field(..., ge=0)

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, payload: str | bytes) -> "LiveCountUpdate":
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return cls.model_validate_json(payload)
