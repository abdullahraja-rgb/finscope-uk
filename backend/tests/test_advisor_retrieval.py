from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.advisor_retrieval import (
    CHUNK_OVERLAP_WORDS,
    MAX_CHUNK_WORDS,
    chunk_markdown,
    retrieve_advisor_chunks,
)


DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"


def long_section_markdown(paragraphs: int = 10, words: int = 50) -> str:
    # Every paragraph uses unique tokens so overlap between windows is provable.
    blocks = "\n\n".join(
        " ".join(f"para{index}word{position}" for position in range(words))
        for index in range(paragraphs)
    )
    return f"# Doc\n\n## Big Section\n\n{blocks}"


def chunk_body(text: str) -> str:
    return text.split("\n\n", 1)[1]


def test_chunk_markdown_splits_by_headings() -> None:
    chunks = chunk_markdown(
        "example.md",
        "# Main Title\n\nIntro text.\n\n## First Section\n\nFirst body.\n\n## Second Section\n\nSecond body.",
    )

    assert [chunk.title for chunk in chunks] == ["Main Title", "First Section", "Second Section"]
    assert chunks[1].heading_path == ("Main Title", "First Section")
    assert "First body." in chunks[1].text


def test_chunk_markdown_bounds_long_sections() -> None:
    chunks = chunk_markdown("example.md", long_section_markdown())
    windows = [chunk for chunk in chunks if chunk.title == "Big Section"]

    assert len(windows) > 1  # a 500-word section no longer becomes one chunk
    for chunk in windows:
        assert len(chunk_body(chunk.text).split()) <= MAX_CHUNK_WORDS + CHUNK_OVERLAP_WORDS + 60
        assert chunk.heading_path == ("Doc", "Big Section")


def test_chunk_markdown_overlaps_adjacent_windows() -> None:
    chunks = chunk_markdown("example.md", long_section_markdown())
    bodies = [chunk_body(chunk.text) for chunk in chunks if chunk.title == "Big Section"]

    shared = set(bodies[0].split()) & set(bodies[1].split())
    assert shared  # trailing content is carried into the next window


def test_chunk_markdown_keeps_short_sections_whole() -> None:
    chunks = chunk_markdown("example.md", "# Doc\n\n## Small\n\nJust a short body.")
    small = [chunk for chunk in chunks if chunk.title == "Small"]

    assert len(small) == 1


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
