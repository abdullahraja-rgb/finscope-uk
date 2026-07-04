from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.advisor_retrieval import chunk_markdown, retrieve_advisor_chunks


DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"


def test_chunk_markdown_splits_by_headings() -> None:
    chunks = chunk_markdown(
        "example.md",
        "# Main Title\n\nIntro text.\n\n## First Section\n\nFirst body.\n\n## Second Section\n\nSecond body.",
    )

    assert [chunk.title for chunk in chunks] == ["Main Title", "First Section", "Second Section"]
    assert chunks[1].heading_path == ("Main Title", "First Section")
    assert "First body." in chunks[1].text


def test_retrieve_inflation_question_returns_cost_of_living_doc() -> None:
    response = retrieve_advisor_chunks(
        "Why is inflation affecting my personal budget?",
        docs_dir=str(DOCS_DIR),
        max_chunks=3,
    )

    assert response.chunks
    assert response.chunks[0].source == "cost-of-living-engine.md"
    assert "inflation" in response.chunks[0].tags


def test_retrieve_time_split_question_returns_forecasting_doc() -> None:
    response = retrieve_advisor_chunks(
        "Why can I not use a random train test split for forecasting?",
        docs_dir=str(DOCS_DIR),
        max_chunks=3,
    )

    sources = [chunk.source for chunk in response.chunks]
    assert "spend-forecasting.md" in sources


def test_retrieve_health_score_question_returns_health_doc() -> None:
    response = retrieve_advisor_chunks(
        "What does my financial health score mean?",
        docs_dir=str(DOCS_DIR),
        max_chunks=3,
    )

    assert response.chunks
    assert response.chunks[0].source == "financial-health-score.md"


def test_retrieve_source_filter_limits_documents() -> None:
    response = retrieve_advisor_chunks(
        "What does my health score mean?",
        docs_dir=str(DOCS_DIR),
        sources=["advisor-context.md"],
    )

    assert response.chunks
    assert {chunk.source for chunk in response.chunks} == {"advisor-context.md"}


def test_retrieve_endpoint_returns_citation_ready_chunks() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/advisor/retrieve",
        json={"question": "How does Bank Rate affect my debt?", "max_chunks": 2},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "How does Bank Rate affect my debt?"
    assert payload["chunks"]
    assert {"id", "title", "source", "heading_path", "text", "score", "tags"}.issubset(
        payload["chunks"][0].keys()
    )
