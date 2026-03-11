from pydantic import BaseModel, ConfigDict


class QualityRuleBase(BaseModel):
    dimension: str
    weight: float = 1.0
    min_score: float = 0.0
    required_status: str | None = None
    scope_category_id: str | None = None


class QualityRuleCreate(QualityRuleBase):
    pass


class QualityRuleRead(QualityRuleBase):
    id: str
    model_config = ConfigDict(from_attributes=True)


class QualityRuleSetBase(BaseModel):
    name: str
    description: str | None = None
    active: bool = False


class QualityRuleSetCreate(QualityRuleSetBase):
    rules: list[QualityRuleCreate] = []


class QualityRuleSetUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class QualityRuleUpdate(BaseModel):
    weight: float | None = None
    min_score: float | None = None
    required_status: str | None = None


class QualityRuleSetRead(QualityRuleSetBase):
    id: str
    rules: list[QualityRuleRead] = []
    model_config = ConfigDict(from_attributes=True)

