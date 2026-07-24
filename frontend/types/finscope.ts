export type Metric = {
  label: string;
  value: string;
  delta: string;
  tone: "good" | "watch" | "risk" | "neutral";
};

export type CategorySpend = {
  category: string;
  spend: number;
  forecast: number;
};

export type InflationImpact = {
  category: string;
  personal: number;
  national: number;
};

export type OnboardingProfile = {
  monthlyIncome: number;
  liquidSavings: number;
  monthlyDebtPayment: number;
  rentOrMortgage: number;
  investmentBalance: number;
  pensionBalance: number;
  propertyValue: number;
  mortgageBalance: number;
  creditCardBalance: number;
  loanBalance: number;
  averageDebtApr: number;
  emergencyFundTarget: number;
  savingsGoalTarget: number;
  monthlyGoalContribution: number;
};

export type TransactionPayload = {
  date: string;
  description: string;
  amount: number;
  category?: string | null;
  transaction_type?: string | null;
  account?: string | null;
};

export type CategorisedTransaction = TransactionPayload & {
  predicted_category: string;
  confidence: number;
};

export type CategorisationResponse = {
  transactions: CategorisedTransaction[];
};

export type CategorisationMetric = {
  category: string;
  precision: number;
  recall: number;
  f1: number;
  support: number;
};

export type ConfusionMatrixRow = {
  actual: string;
  predicted: Record<string, number>;
};

export type MisclassifiedTransaction = {
  description: string;
  amount: number;
  actual_category: string;
  predicted_category: string;
};

export type CategorisationEvaluationResponse = {
  training_rows: number;
  test_rows: number;
  accuracy: number;
  macro_f1: number;
  weighted_f1: number;
  per_class: CategorisationMetric[];
  confusion_matrix: ConfusionMatrixRow[];
  misclassified: MisclassifiedTransaction[];
};

export type TransactionPreviewResponse = {
  rows: number;
  columns: string[];
  total_income: number;
  total_spend: number;
  preview: Record<string, unknown>[];
};

export type ForecastPoint = {
  category: string;
  expected_spend: number;
  lower_bound: number;
  upper_bound: number;
  model: string;
  baseline_expected_spend: number | null;
  error_margin: number | null;
  backtest_mae: number | null;
  baseline_mae: number | null;
  beats_baseline: boolean | null;
};

export type ForecastResponse = {
  period: string;
  forecasts: ForecastPoint[];
  baseline: string;
  generated_from_months: number;
  notes: string[];
};

export type ForecastMetric = {
  category: string;
  model: string;
  baseline: string;
  windows: number;
  mae: number;
  rmse: number;
  mape: number | null;
  baseline_mae: number;
  beats_baseline: boolean;
};

export type ForecastBacktestResponse = {
  baseline: string;
  candidate_models: string[];
  metrics: ForecastMetric[];
  notes: string[];
};

export type LatestInflationCategory = {
  index_type: string;
  date: string;
  coicop_code: string | null;
  category: string;
  category_level: string;
  weight: number | null;
  annual_change_pct: number;
};

export type LatestInflationResponse = {
  index_type: string;
  date: string | null;
  categories: LatestInflationCategory[];
};

export type PersonalInflationCategory = {
  app_category: string;
  spend: number;
  spend_share: number;
  ons_category: string | null;
  coicop_code: string | null;
  annual_change_pct: number | null;
  contribution_pct_points: number | null;
};

export type PersonalInflationResponse = {
  index_type: string;
  period: string;
  total_spend: number;
  personal_inflation_pct: number;
  national_inflation_pct: number;
  difference_pct_points: number;
  categories: PersonalInflationCategory[];
  notes: string[];
};

export type RateImpactRequest = {
  savings_balance: number;
  variable_debt_balance: number;
  mortgage_balance?: number;
  mortgage_years_remaining?: number;
  current_mortgage_rate_pct?: number | null;
  bank_rate_change_pct_points?: number;
  pass_through_pct?: number;
};

export type RateImpactLine = {
  name: string;
  monthly_delta: number;
  annual_delta: number;
  note: string;
};

export type RateImpactResponse = {
  current_bank_rate_pct: number;
  scenario_bank_rate_pct: number;
  bank_rate_change_pct_points: number;
  effective_rate_change_pct_points: number;
  monthly_net_cashflow_delta: number;
  annual_net_cashflow_delta: number;
  lines: RateImpactLine[];
  notes: string[];
};

export type ScoreComponent = {
  name: string;
  score: number;
  weight: number;
  note: string;
};

export type SpendingBenchmark = {
  coicop_code: string;
  ons_category: string;
  user_share: number;
  benchmark_share: number;
  difference_pct_points: number;
  note: string;
};

export type DerivedHealthScoreRequest = {
  transactions: TransactionPayload[];
  monthly_income?: number | null;
  liquid_savings?: number;
  monthly_debt_payment?: number;
  rent_or_mortgage?: number | null;
};

export type DerivedHealthScoreResponse = {
  score: number;
  band: string;
  components: ScoreComponent[];
  monthly_income: number;
  monthly_spend: number;
  savings_rate: number;
  rent_to_income: number;
  emergency_fund_months: number;
  spending_volatility: number;
  benchmarks: SpendingBenchmark[];
  notes: string[];
};

export type Recommendation = {
  title: string;
  detail: string;
  action: string;
  priority: "high" | "medium" | "low" | string;
  source: string;
};

export type RecommendationsRequest = {
  forecast?: ForecastResponse | null;
  personal_inflation?: PersonalInflationResponse | null;
  health_score?: DerivedHealthScoreResponse | null;
  rate_impact?: RateImpactResponse | null;
};

export type RecommendationsResponse = {
  recommendations: Recommendation[];
};

export type AdvisorProfile = {
  monthly_income: number;
  rent_or_mortgage: number;
  monthly_debt_payment: number;
  liquid_savings: number;
  investment_balance: number;
  pension_balance: number;
  property_value: number;
  mortgage_balance: number;
  credit_card_balance: number;
  loan_balance: number;
  average_debt_apr: number;
  emergency_fund_target: number;
  savings_goal_target: number;
  monthly_goal_contribution: number;
};

export type AdvisorMissingData = {
  key: string;
  label: string;
  reason: string;
  impact: string;
  action: string;
};

export type AdvisorKnowledgeChunk = {
  id: string;
  title: string;
  source: string;
  /** Plain-English source name. Render this, never `source` or `title`. */
  source_label: string;
  heading_path: string[];
  text: string;
  /** Display copy without the internal heading breadcrumb. */
  body: string;
  score: number;
  tags: string[];
};

export type AdvisorCitation = {
  source: string;
  /** Plain-English source name. Render this, never `source` or `title`. */
  source_label: string;
  title: string;
  chunk_id: string;
  heading_path: string[];
};

export type AdvisorAskRequest = {
  question: string;
  max_chunks?: number;
  min_retrieval_score?: number;
  profile?: AdvisorProfile | null;
  transactions?: TransactionPayload[];
  forecast?: ForecastResponse | null;
  personal_inflation?: PersonalInflationResponse | null;
  health_score?: DerivedHealthScoreResponse | null;
  rate_impact?: RateImpactResponse | null;
  recommendations?: Recommendation[];
};

export type AdvisorAskResponse = {
  answer: string;
  summary_bullets: string[];
  citations: AdvisorCitation[];
  used_numbers: string[];
  missing_data: AdvisorMissingData[];
  retrieved_chunks: AdvisorKnowledgeChunk[];
  guardrails: string[];
  confidence: string;
  provider: string;
  notes: string[];
};

export type TransactionAnalysisResponse = TransactionPreviewResponse & {
  transactions: CategorisedTransaction[];
  forecast: ForecastResponse;
  personal_inflation: PersonalInflationResponse | null;
  health_score: DerivedHealthScoreResponse | null;
  recommendations: Recommendation[];
  notes: string[];
};
