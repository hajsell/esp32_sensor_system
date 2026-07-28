from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

SensorMetric = Literal[
    "temperature",
    "humidity",
    "mq2",
    "mq7",
]


class HistoryMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Treść wiadomości nie może być pusta.")
        return value


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=2000)
    history: list[HistoryMessage] = Field(
        default_factory=list,
        max_length=10,
    )

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Wiadomość nie może być pusta.")
        return value


class WarningThresholds(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        allow_inf_nan=False,
    )

    temperature: float = Field(ge=-50, le=100)
    humidity: float = Field(ge=0, le=100)
    mq2: float = Field(ge=0, le=4095)
    mq7: float = Field(ge=0, le=4095)


class ThresholdsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    warning: WarningThresholds


class SensorSummaryArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric: SensorMetric
    hours: int = Field(ge=1, le=168)


class CurrentReadingArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")