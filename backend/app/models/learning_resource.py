from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.data.learning_resource_catalog import (
    LearningResourceLevel,
    LearningResourceType,
)


class LearningResourceResponse(BaseModel):
    """API representation of one curated learning resource."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(min_length=1)
    skill: str = Field(min_length=1)
    title: str = Field(min_length=1)
    url: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    resource_type: LearningResourceType
    level: LearningResourceLevel


class LearningResourceLookupResponse(BaseModel):
    """Curated resources associated with one skill."""

    skill: str = Field(min_length=1)
    total_resources: int = Field(ge=0)
    resources: list[LearningResourceResponse] = Field(
        default_factory=list,
    )

    @model_validator(mode="after")
    def validate_total_resources(
        self,
    ) -> "LearningResourceLookupResponse":
        if self.total_resources != len(self.resources):
            raise ValueError(
                "total_resources must equal the number of resources."
            )
        return self