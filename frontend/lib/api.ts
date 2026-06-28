import type {
  LatestInflationResponse,
  DerivedHealthScoreRequest,
  DerivedHealthScoreResponse,
  PersonalInflationResponse,
  RateImpactRequest,
  RateImpactResponse,
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

export async function uploadTransactions(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/v1/transactions/preview`, {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(payload.detail ?? "Upload failed");
  }

  return response.json();
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
