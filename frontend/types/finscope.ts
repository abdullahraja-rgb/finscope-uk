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

export type TransactionPayload = {
  date: string;
  description: string;
  amount: number;
  category?: string | null;
  transaction_type?: string | null;
  account?: string | null;
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
