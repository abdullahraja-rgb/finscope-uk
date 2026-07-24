import re
from pathlib import Path

from app.schemas.transactions import AdvisorAskRequest
from app.services.advisor_answer import answer_advisor_question
from app.services.advisor_eval import EVAL_CASES
from app.services.advisor_extractive import is_user_friendly
from tests.test_advisor_context import full_context_request


DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"

# Terminology that must never reach a dashboard user.
BANNED_SUBSTRINGS = (
    ".md",
    "snake_case",
    "http",
    "/api",
    "`",
    "chunk",
    "endpoint",
    "backend",
    "schema",
    "json",
    "methodology",
    "context pack",
    "deterministic",
    "retrieval",
    "embedding",
    "llm",
    "prompt",
    "transaction row",
    "data gap",
    "supplied finscope",
)

SNAKE_CASE_PATTERN = re.compile(r"\b[a-z]+_[a-z_]+\b")
ALLOWED_ACRONYMS = {"GBP", "UK", "ONS", "CPI", "CPIH", "APR", "ISA", "CSV", "PDF"}
ACRONYM_PATTERN = re.compile(r"\b[A-Z]{2,6}\b")


def user_facing_text(response) -> list[str]:
    """Every string the advisor panel actually renders.

    Internal document headings (``title``) and filenames (``source``) stay in
    the payload for debugging but are never rendered, so they are not asserted
    on here - the UI shows ``source_label`` instead.
    """
    texts = [response.answer, *response.summary_bullets, *response.used_numbers]
    for item in response.missing_data:
        texts.extend([item.label, item.impact, item.action])
    for citation in response.citations:
        texts.append(citation.source_label)
    for chunk in response.retrieved_chunks:
        texts.append(chunk.source_label)
    return [text for text in texts if text]


def answers_for_eval_set():
    for case in EVAL_CASES:
        payload = full_context_request().model_dump()
        payload["question"] = case.question
        yield case.question, answer_advisor_question(
            AdvisorAskRequest(**payload), docs_dir=str(DOCS_DIR)
        )


def test_no_internal_terminology_in_user_facing_text() -> None:
    for question, response in answers_for_eval_set():
        for text in user_facing_text(response):
            lowered = text.lower()
            for banned in BANNED_SUBSTRINGS:
                assert banned not in lowered, f"{question!r} leaked {banned!r} in: {text}"


def test_no_snake_case_or_unknown_acronyms_in_user_facing_text() -> None:
    for question, response in answers_for_eval_set():
        for text in user_facing_text(response):
            assert not SNAKE_CASE_PATTERN.search(text), f"{question!r} leaked an internal name: {text}"
            unknown = [item for item in ACRONYM_PATTERN.findall(text) if item not in ALLOWED_ACRONYMS]
            assert not unknown, f"{question!r} leaked acronyms {unknown} in: {text}"


def test_citations_expose_friendly_labels_not_filenames() -> None:
    _question, response = next(iter(answers_for_eval_set()))

    assert response.citations
    for citation in response.citations:
        assert citation.source_label
        assert not citation.source_label.endswith(".md")
        assert citation.source_label != citation.source
    for chunk in response.retrieved_chunks:
        assert chunk.source_label and not chunk.source_label.endswith(".md")
        assert chunk.body and not chunk.body.startswith(chunk.heading_path[0])


def test_no_formulas_or_third_person_framing() -> None:
    for question, response in answers_for_eval_set():
        for text in user_facing_text(response):
            assert "=" not in text, f"{question!r} leaked a formula in: {text}"
            assert "sum(" not in text.lower(), f"{question!r} leaked a formula in: {text}"
            # The advisor talks to the reader, never about "the user".
            assert not re.search(r"\bthe users?\b", text, re.IGNORECASE), (
                f"{question!r} referred to the reader in third person: {text}"
            )


def test_is_user_friendly_screens_engineering_text() -> None:
    assert is_user_friendly("Your spending is compared against last month to spot changes.")
    assert not is_user_friendly("The API reports MAE and RMSE for each candidate.")
    assert not is_user_friendly("Savings and variable debt use simple monthly interest deltas:")
    assert not is_user_friendly("The advisor_context module builds the pack.")
    assert not is_user_friendly("personal inflation = sum(category spend share * rate).")
    assert not is_user_friendly("I weight the inflation rate by the user's own spending mix.")
