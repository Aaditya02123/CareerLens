from typing import Literal

from pydantic import BaseModel, Field, model_validator


LearningEffortGapStatus = Literal["partial", "missing"]


class LearningEffortResponse(BaseModel):
    """Indicative deterministic effort estimate for one roadmap skill."""

    skill: str = Field(min_length=1)
    gap_status: LearningEffortGapStatus
    minimum_hours: int | None = Field(default=None, ge=1)
    maximum_hours: int | None = Field(default=None, ge=1)
    available: bool

    @model_validator(mode="after")
    def validate_availability(self) -> "LearningEffortResponse":
        if self.available:
            if (
                self.minimum_hours is None
                or self.maximum_hours is None
            ):
                raise ValueError(
                    "Available estimates must include minimum and "
                    "maximum hours."
                )

            if self.minimum_hours > self.maximum_hours:
                raise ValueError(
                    "Minimum hours cannot exceed maximum hours."
                )

        elif (
            self.minimum_hours is not None
            or self.maximum_hours is not None
        ):
            raise ValueError(
                "Unavailable estimates must not include hour values."
            )

        return self