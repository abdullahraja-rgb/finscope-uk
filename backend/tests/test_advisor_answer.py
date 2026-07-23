from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.transactions import AdvisorAskRequest
from app.services.advisor_answer import answer_advisor_question, build_advisor_prompt
from app.services.advisor_context import build_advisor_context
from app.services.advisor_llm import OpenAIResponsesAdvisorClient, OpenAIResponsesConfig
from app.services.advisor_retrieval import retrieve_advisor_chunks
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
    assert any("Monthly spend: GBP 1,420" == item for item in response.used_numbers)
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


def openai_config() -> OpenAIResponsesConfig:
    return OpenAIResponsesConfig(
        api_key="test-key",
        model="test-model",
        base_url="https://example.test/v1",
        timeout_seconds=5,
        max_output_tokens=500,
        temperature=0.2,
    )


def llm_inputs():
    request = ask_request("What should I fix first?")
    context = build_advisor_context(request)
    chunks = retrieve_advisor_chunks(
        question=request.question,
        docs_dir=str(DOCS_DIR),
        max_chunks=request.max_chunks,
        min_score=request.min_retrieval_score,
    ).chunks
    prompt = build_advisor_prompt(request, context, chunks)
    return request, context, chunks, prompt


def test_openai_responses_client_returns_validated_answer() -> None:
    request, context, chunks, prompt = llm_inputs()
    first_chunk_id = chunks[0].id

    def fake_post_json(url, headers, json_body, timeout_seconds):
        assert url == "https://example.test/v1/responses"
        assert headers["Authorization"] == "Bearer test-key"
        assert json_body["text"]["format"]["type"] == "json_schema"
        assert timeout_seconds == 5
        return {
            "output_text": (
                '{"answer":"Monthly spend is GBP 1,420, so I would start with the weakest score driver.",'
                '"summary_bullets":["Monthly spend is GBP 1,420."],'
                f'"citation_chunk_ids":["{first_chunk_id}"],'
                '"used_numbers":["Monthly spend: GBP 1,420"],'
                '"confidence":"high"}'
            )
        }

    client = OpenAIResponsesAdvisorClient(openai_config(), post_json=fake_post_json)
    response = client.answer(request, context, chunks, prompt)

    assert response.provider == "openai_responses"
    assert response.answer.startswith("Monthly spend is GBP 1,420")
    assert response.used_numbers == ["Monthly spend: GBP 1,420"]
    assert response.citations[0].chunk_id == first_chunk_id
    assert response.missing_data == context.missing_data


def test_openai_responses_client_falls_back_when_answer_invents_number() -> None:
    request, context, chunks, prompt = llm_inputs()

    def fake_post_json(url, headers, json_body, timeout_seconds):
        return {
            "output_text": (
                '{"answer":"You should save GBP 999 next month.",'
                '"summary_bullets":["Set aside GBP 999."],'
                f'"citation_chunk_ids":["{chunks[0].id}"],'
                '"used_numbers":[],'
                '"confidence":"high"}'
            )
        }

    client = OpenAIResponsesAdvisorClient(openai_config(), post_json=fake_post_json)
    response = client.answer(request, context, chunks, prompt)

    assert response.provider == "deterministic_fallback"
    assert "unsupported numbers" in response.notes[0]
