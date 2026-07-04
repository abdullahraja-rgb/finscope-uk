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


class TransactionPreviewResponse(BaseModel):
    rows: int
    columns: list[str]
    total_income: float
    total_spend: float
    preview: list[dict[str, object]]


class CategorisationEvaluationRequest(TransactionBatch):
    test_size: float = Field(default=0.25, ge=0.1, le=0.5)
    random_state: int = 42


class CategorisationMetric(BaseModel):
    category: str
    precision: float
    recall: float
    f1: float
    support: int


class ConfusionMatrixRow(BaseModel):
    actual: str
    predicted: dict[str, int]


class MisclassifiedTransaction(BaseModel):
    description: str
    amount: float
    actual_category: str
    predicted_category: str


class CategorisationEvaluationResponse(BaseModel):
    training_rows: int
    test_rows: int
    accuracy: float
    macro_f1: float
    weighted_f1: float
    per_class: list[CategorisationMetric]
    confusion_matrix: list[ConfusionMatrixRow]
    misclassified: list[MisclassifiedTransaction]


class ForecastPoint(BaseModel):
    category: str
    expected_spend: float
    lower_bound: float
    upper_bound: float
    model: str = "three-month moving average"
    baseline_expected_spend: float | None = None
    error_margin: float | None = None
    backtest_mae: float | None = None
    baseline_mae: float | None = None
    beats_baseline: bool | None = None


class ForecastResponse(BaseModel):
    period: str
    forecasts: list[ForecastPoint]
    baseline: str
    generated_from_months: int = 0
    notes: list[str] = Field(default_factory=list)


class ForecastBacktestRequest(TransactionBatch):
    min_train_months: int = Field(default=4, ge=2, le=24)


class ForecastMetric(BaseModel):
    category: str
    model: str
    baseline: str
    windows: int
    mae: float
    rmse: float
    mape: float | None
    baseline_mae: float
    beats_baseline: bool


class ForecastBacktestResponse(BaseModel):
    baseline: str
    candidate_models: list[str]
    metrics: list[ForecastMetric]
    notes: list[str]


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


class SpendingBenchmark(BaseModel):
    coicop_code: str
    ons_category: str
    user_share: float
    benchmark_share: float
    difference_pct_points: float
    note: str


class DerivedHealthScoreRequest(TransactionBatch):
    monthly_income: float | None = Field(default=None, gt=0)
    liquid_savings: float = Field(default=0, ge=0)
    monthly_debt_payment: float = Field(default=0, ge=0)
    rent_or_mortgage: float | None = Field(default=None, ge=0)


class DerivedHealthScoreResponse(HealthScoreResponse):
    monthly_income: float
    monthly_spend: float
    savings_rate: float
    rent_to_income: float
    emergency_fund_months: float
    spending_volatility: float
    benchmarks: list[SpendingBenchmark]
    notes: list[str]


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


class PersonalInflationRequest(TransactionBatch):
    index_type: str = "cpih"


class PersonalInflationCategory(BaseModel):
    app_category: str
    spend: float
    spend_share: float
    ons_category: str | None
    coicop_code: str | None
    annual_change_pct: float | None
    contribution_pct_points: float | None


class PersonalInflationResponse(BaseModel):
    index_type: str
    period: str
    total_spend: float
    personal_inflation_pct: float
    national_inflation_pct: float
    difference_pct_points: float
    categories: list[PersonalInflationCategory]
    notes: list[str]


class RateImpactRequest(BaseModel):
    savings_balance: float = Field(ge=0)
    variable_debt_balance: float = Field(ge=0)
    mortgage_balance: float = Field(default=0, ge=0)
    mortgage_years_remaining: float = Field(default=25, gt=0)
    current_mortgage_rate_pct: float | None = Field(default=None, ge=0)
    bank_rate_change_pct_points: float = 0.25
    pass_through_pct: float = Field(default=100, ge=0, le=200)


class RateImpactLine(BaseModel):
    name: str
    monthly_delta: float
    annual_delta: float
    note: str


class RateImpactResponse(BaseModel):
    current_bank_rate_pct: float
    scenario_bank_rate_pct: float
    bank_rate_change_pct_points: float
    effective_rate_change_pct_points: float
    monthly_net_cashflow_delta: float
    annual_net_cashflow_delta: float
    lines: list[RateImpactLine]
    notes: list[str]


class Recommendation(BaseModel):
    title: str
    detail: str
    action: str
    priority: str
    source: str


class RecommendationsRequest(BaseModel):
    forecast: ForecastResponse | None = None
    personal_inflation: PersonalInflationResponse | None = None
    health_score: DerivedHealthScoreResponse | None = None
    rate_impact: RateImpactResponse | None = None


class RecommendationsResponse(BaseModel):
    recommendations: list[Recommendation]


class AdvisorProfile(BaseModel):
    monthly_income: float = Field(default=0, ge=0)
    rent_or_mortgage: float = Field(default=0, ge=0)
    monthly_debt_payment: float = Field(default=0, ge=0)
    liquid_savings: float = Field(default=0, ge=0)
    investment_balance: float = Field(default=0, ge=0)
    pension_balance: float = Field(default=0, ge=0)
    property_value: float = Field(default=0, ge=0)
    mortgage_balance: float = Field(default=0, ge=0)
    credit_card_balance: float = Field(default=0, ge=0)
    loan_balance: float = Field(default=0, ge=0)
    average_debt_apr: float = Field(default=0, ge=0)
    emergency_fund_target: float = Field(default=0, ge=0)
    savings_goal_target: float = Field(default=0, ge=0)
    monthly_goal_contribution: float = Field(default=0, ge=0)


class AdvisorFact(BaseModel):
    id: str
    label: str
    value: float | str | bool | None
    formatted: str
    source: str
    citation: str
    unit: str | None = None


class AdvisorContextSection(BaseModel):
    id: str
    title: str
    facts: list[AdvisorFact] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class AdvisorMissingData(BaseModel):
    key: str
    label: str
    reason: str
    impact: str
    action: str


class AdvisorContextRequest(BaseModel):
    question: str | None = None
    profile: AdvisorProfile | None = None
    transactions: list[TransactionIn] = Field(default_factory=list)
    forecast: ForecastResponse | None = None
    personal_inflation: PersonalInflationResponse | None = None
    health_score: DerivedHealthScoreResponse | None = None
    rate_impact: RateImpactResponse | None = None
    recommendations: list[Recommendation] = Field(default_factory=list)


class AdvisorContextResponse(BaseModel):
    context_markdown: str
    sections: list[AdvisorContextSection]
    missing_data: list[AdvisorMissingData]
    allowed_numbers: list[str]
    source_map: dict[str, str]
    guardrails: list[str]


class TransactionAnalysisResponse(TransactionPreviewResponse):
    transactions: list[CategorisedTransaction]
    forecast: ForecastResponse
    personal_inflation: PersonalInflationResponse | None = None
    health_score: DerivedHealthScoreResponse | None = None
    recommendations: list[Recommendation] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
