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
