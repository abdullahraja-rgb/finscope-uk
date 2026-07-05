from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.transactions import AdvisorAskRequest
from app.services.advisor_answer import answer_advisor_question
from tests.test_advisor_context import full_context_request


DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"


def ask_request(question: str = "Why is my budget under pressure?") -> AdvisorAskRequest:
    payload = full_context_request().model_dump()
    payload["question"] = question
    return AdvisorAskRequest(**payload)


def test_answer_advisor_question_returns_grounded_response() -> None:
    response = answer_advisor_question(ask_request(), docs_dir=str(DOCS_DIR))

    assert response.provider == "deterministic_fallback"
    assert response.summary_bullets
    assert response.citations
    assert response.retrieved_chunks
    assert any("Monthly spend: GBP 1,420 [health_score]" == item for item in response.used_numbers)
    assert "GBP 1,780" in response.answer
    assert "supplied FinScope facts" in response.answer
    assert all(citation.source.endswith(".md") for citation in response.citations)


def test_answer_advisor_question_reports_missing_data() -> None:
    request = ask_request()
    response = answer_advisor_question(
        request=request.model_copy(
            update={
                "transactions": [],
                "forecast": None,
                "personal_inflation": None,
                "health_score": None,
                "rate_impact": None,
            }
        ),
        docs_dir=str(DOCS_DIR),
    )

    missing_keys = {item.key for item in response.missing_data}
    assert "transactions" in missing_keys
    assert "forecast" in missing_keys
    assert "personal_inflation" in missing_keys
    assert response.confidence in {"low", "medium"}
    assert "partial view" in response.answer


def test_advisor_ask_endpoint_returns_structured_answer() -> None:
    client = TestClient(app)
    request = ask_request("How is inflation affecting my budget?")

    response = client.post("/api/v1/advisor/ask", json=request.model_dump(mode="json"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"]
    assert payload["provider"] == "deterministic_fallback"
    assert payload["citations"]
    assert payload["used_numbers"]
    assert payload["guardrails"]
