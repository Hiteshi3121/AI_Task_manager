from agents.brief_agent import _build_prompt


def _task(priority, due, title="Task"):
    return {"priority": priority, "due": due, "title": title, "bucket_id": "udukku"}


def test_bullet_target_floors_at_eight_when_quiet():
    prompt = _build_prompt([_task("low", "no deadline")], [])
    assert "aim for 8 bullets" in prompt


def test_bullet_target_scales_with_urgent_count():
    tasks = [_task("high", "today") for _ in range(10)]
    prompt = _build_prompt(tasks, [])
    assert "aim for 10 bullets" in prompt


def test_bullet_target_caps_at_twelve():
    tasks = [_task("high", "today") for _ in range(20)]
    prompt = _build_prompt(tasks, [])
    assert "aim for 12 bullets" in prompt


def test_prompt_forbids_inventing_tasks():
    prompt = _build_prompt([_task("low", "no deadline")], [])
    assert "never invent a task" in prompt
    assert "only 1 open tasks total" in prompt
