from datetime import date

from pydantic import BaseModel, Field


class TransactionIn(BaseModel):
    date: date
    description: str = Field(min_length=1)
    amount: float
    category: str | None = None
    transaction_type: str | None = None
    account: str | None = None


class TransactionBatch(BaseModel):
    transactions: list[TransactionIn] = Field(default_factory=list)


class CategorisedTransaction(TransactionIn):
    predicted_category: str
    confidence: float = Field(ge=0, le=1)


class CategorisationResponse(BaseModel):
    transactions: list[CategorisedTransaction]


class ForecastPoint(BaseModel):
    category: str
    expected_spend: float
    lower_bound: float
    upper_bound: float


class ForecastResponse(BaseModel):
    period: str
    forecasts: list[ForecastPoint]
    baseline: str


class HealthScoreRequest(BaseModel):
    monthly_income: float = Field(gt=0)
    monthly_spend: float = Field(ge=0)
    rent_or_mortgage: float = Field(ge=0)
    monthly_debt_payment: float = Field(ge=0)
    liquid_savings: float = Field(ge=0)
    subscriptions: float = Field(ge=0)
    spend_volatility: float = Field(ge=0, description="Monthly spend standard deviation.")


class ScoreComponent(BaseModel):
    name: str
    score: float
    weight: float
    note: str


class HealthScoreResponse(BaseModel):
    score: float
    band: str
    components: list[ScoreComponent]


class ScenarioRequest(BaseModel):
    monthly_income: float = Field(gt=0)
    monthly_spend: float = Field(ge=0)
    rent_or_mortgage: float = Field(ge=0)
    savings_balance: float = Field(ge=0)
    variable_debt_balance: float = Field(ge=0)
    food_spend: float = Field(ge=0)
    rent_change_pct: float = 0
    food_change_pct: float = 0
    bank_rate_change_pct_points: float = 0


class ScenarioResponse(BaseModel):
    new_monthly_spend: float
    disposable_income: float
    savings_interest_delta_monthly: float
    debt_cost_delta_monthly: float
    notes: list[str]
