import type {
  CategorisationEvaluationResponse,
  CategorisationResponse,
  DerivedHealthScoreRequest,
  DerivedHealthScoreResponse,
  ForecastBacktestResponse,
  ForecastResponse,
  LatestInflationResponse,
  OnboardingProfile,
  PersonalInflationResponse,
  RateImpactRequest,
  RateImpactResponse,
  RecommendationsRequest,
  RecommendationsResponse,
  TransactionAnalysisResponse,
  TransactionPayload
} from "@/types/finscope";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function getHealth() {
  const response = await fetch(`${API_BASE_URL}/health`, {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error("API health check failed");
  }

  return response.json() as Promise<{ status: string }>;
}

export async function uploadTransactions(file: File, profile?: OnboardingProfile) {
  const formData = new FormData();
  formData.append("file", file);
  if (profile) {
    if (profile.monthlyIncome > 0) {
      formData.append("monthly_income", profile.monthlyIncome.toString());
    }
    formData.append("liquid_savings", profile.liquidSavings.toString());
    formData.append("monthly_debt_payment", profile.monthlyDebtPayment.toString());
    formData.append("rent_or_mortgage", profile.rentOrMortgage.toString());
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/transactions/analyse`, {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(payload.detail ?? "Upload failed");
  }

  return response.json() as Promise<TransactionAnalysisResponse>;
}

export async function getLatestInflation(indexType = "cpih") {
  const params = new URLSearchParams({ index_type: indexType });
  const response = await fetch(`${API_BASE_URL}/api/v1/datasets/inflation/latest?${params}`, {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error("Latest inflation data unavailable");
  }

  return response.json() as Promise<LatestInflationResponse>;
}

export async function categoriseTransactions(transactions: TransactionPayload[]) {
  const response = await fetch(`${API_BASE_URL}/api/v1/categorise`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ transactions })
  });

  if (!response.ok) {
    throw new Error("Transaction categorisation failed");
  }

  return response.json() as Promise<CategorisationResponse>;
}

export async function evaluateCategorisationModel(
  transactions: TransactionPayload[],
  testSize = 0.25,
  randomState = 42
) {
  const response = await fetch(`${API_BASE_URL}/api/v1/categorise/evaluate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      transactions,
      test_size: testSize,
      random_state: randomState
    })
  });

  if (!response.ok) {
    throw new Error("Categorisation evaluation failed");
  }

  return response.json() as Promise<CategorisationEvaluationResponse>;
}

export async function calculateForecast(transactions: TransactionPayload[]) {
  const response = await fetch(`${API_BASE_URL}/api/v1/forecast`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ transactions })
  });

  if (!response.ok) {
    throw new Error("Forecast calculation failed");
  }

  return response.json() as Promise<ForecastResponse>;
}

export async function backtestForecast(transactions: TransactionPayload[], minTrainMonths = 4) {
  const response = await fetch(`${API_BASE_URL}/api/v1/forecast/backtest`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      transactions,
      min_train_months: minTrainMonths
    })
  });

  if (!response.ok) {
    throw new Error("Forecast backtest failed");
  }

  return response.json() as Promise<ForecastBacktestResponse>;
}

export async function calculatePersonalInflation(transactions: TransactionPayload[], indexType = "cpih") {
  const response = await fetch(`${API_BASE_URL}/api/v1/cost-of-living/personal-inflation`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      index_type: indexType,
      transactions
    })
  });

  if (!response.ok) {
    throw new Error("Personal inflation calculation failed");
  }

  return response.json() as Promise<PersonalInflationResponse>;
}

export async function calculateRateImpact(request: RateImpactRequest) {
  const response = await fetch(`${API_BASE_URL}/api/v1/cost-of-living/rate-impact`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(request)
  });

  if (!response.ok) {
    throw new Error("Rate impact calculation failed");
  }

  return response.json() as Promise<RateImpactResponse>;
}

export async function calculateDerivedHealthScore(request: DerivedHealthScoreRequest) {
  const response = await fetch(`${API_BASE_URL}/api/v1/score/from-transactions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(request)
  });

  if (!response.ok) {
    throw new Error("Financial health calculation failed");
  }

  return response.json() as Promise<DerivedHealthScoreResponse>;
}

export async function getRecommendations(request: RecommendationsRequest) {
  const response = await fetch(`${API_BASE_URL}/api/v1/recommendations`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(request)
  });

  if (!response.ok) {
    throw new Error("Recommendations calculation failed");
  }

  return response.json() as Promise<RecommendationsResponse>;
}
