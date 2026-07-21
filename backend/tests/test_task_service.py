from services.task_service import _clamp_due


def test_clamp_due_passes_through_valid_values():
    for value in ["today", "this week", "upcoming", "no deadline"]:
        assert _clamp_due(value) == value


def test_clamp_due_falls_back_on_llm_drift():
    # The classifier is instructed to only ever return one of the four
    # valid values, but LLMs occasionally drift — this is the guardrail
    # that stops a 500 on the DB's check constraint when that happens.
    assert _clamp_due("tomorrow") == "upcoming"
    assert _clamp_due("next Friday") == "upcoming"
    assert _clamp_due("") == "upcoming"
