from pathlib import Path

from app.schemas.transactions import AdvisorAskRequest
from app.services.advisor_answer import answer_advisor_question, select_facts_for_intent
from app.services.advisor_context import build_advisor_context
from app.services.advisor_extractive import extractive_explanation, split_sentences
from app.services.advisor_intent import build_question_intent, detect_intent_kind, route_sections
from app.services.advisor_retrieval import retrieve_advisor_chunks
from tests.test_advisor_context import full_context_request


DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"


def ask(question: str) -> AdvisorAskRequest:
    payload = full_context_request().model_dump()
    payload["question"] = question
    return AdvisorAskRequest(**payload)


def answer_for(question: str):
    return answer_advisor_question(ask(question), docs_dir=str(DOCS_DIR))


def test_route_sections_maps_topic_to_section() -> None:
    assert route_sections("How is my debt and net worth?")[0] == "wealth"
    assert route_sections("Explain my personal inflation")[0] == "inflation"
    assert route_sections("What will I spend next month?")[0] == "forecast"
    assert route_sections("How is my cash flow this month?")[0] == "cash_flow"


def test_detect_intent_kind() -> None:
    assert detect_intent_kind("Why is my budget tight?") == "why"
    assert detect_intent_kind("How much do I owe?") == "how_much"
    assert detect_intent_kind("What should I do about my debt?") == "what_should_i_do"
    assert detect_intent_kind("Tell me about my forecast") == "explain"


def test_select_facts_for_intent_follows_routing() -> None:
    context = build_advisor_context(full_context_request())

    debt_facts = {item.id for item in select_facts_for_intent(context, build_question_intent("How is my debt?"))}
    assert "consumer_debt" in debt_facts
    assert "net_worth" in debt_facts
    assert "personal_inflation" not in debt_facts

    inflation_facts = {item.id for item in select_facts_for_intent(context, build_question_intent("Explain my personal inflation"))}
    assert "personal_inflation" in inflation_facts
    assert "consumer_debt" not in inflation_facts


def test_answers_differ_by_question() -> None:
    # Regression guard for the original bug: every question returned the same body.
    debt = answer_for("How is my debt looking?")
    inflation = answer_for("Explain my personal inflation")
    forecast = answer_for("What will I spend next month?")
    cash = answer_for("How is my cash flow?")

    answers = [debt.answer, inflation.answer, forecast.answer, cash.answer]
    assert len(set(answers)) == 4

    assert "Consumer debt" in debt.answer
    assert "4.2%" in inflation.answer
    assert "GBP 1,260" in forecast.answer
    assert "GBP 1,780" in cash.answer


def test_summary_bullets_track_the_question() -> None:
    debt = answer_for("How is my debt looking?")
    inflation = answer_for("Explain my personal inflation")

    assert any("debt" in bullet.lower() for bullet in debt.summary_bullets)
    assert any("inflation" in bullet.lower() for bullet in inflation.summary_bullets)
    assert debt.summary_bullets != inflation.summary_bullets


def test_extractive_explanation_is_digit_free_and_relevant() -> None:
    request = ask("Why can I not use a random train test split for forecasting?")
    chunks = retrieve_advisor_chunks(
        question=request.question,
        docs_dir=str(DOCS_DIR),
        max_chunks=4,
        min_score=request.min_retrieval_score,
    ).chunks

    picks = extractive_explanation(request.question, chunks, limit=2)
    assert picks
    for sentence, _chunk in picks:
        assert not any(character.isdigit() for character in sentence)


def test_split_sentences_drops_numeric_lines() -> None:
    sentences = split_sentences(
        "Your spending is compared against last month to spot changes.\nThe target error is 12 percent."
    )
    assert any("compared against last month" in sentence for sentence in sentences)
    assert all("12 percent" not in sentence for sentence in sentences)
