from datetime import datetime, timedelta
from services.due_utils import effective_due


def test_today_stays_today_when_created_today():
    assert effective_due("today", datetime.now()) == "today"


def test_today_becomes_overdue_after_a_day():
    created = datetime.now() - timedelta(days=1)
    assert effective_due("today", created) == "overdue"


def test_today_becomes_overdue_after_several_days():
    created = datetime.now() - timedelta(days=5)
    assert effective_due("today", created) == "overdue"


def test_this_week_stays_this_week_within_same_iso_week():
    assert effective_due("this week", datetime.now()) == "this week"


def test_this_week_becomes_overdue_after_a_week():
    created = datetime.now() - timedelta(days=10)
    assert effective_due("this week", created) == "overdue"


def test_upcoming_never_goes_stale():
    created = datetime.now() - timedelta(days=365)
    assert effective_due("upcoming", created) == "upcoming"


def test_no_deadline_never_goes_stale():
    created = datetime.now() - timedelta(days=365)
    assert effective_due("no deadline", created) == "no deadline"


def test_overdue_stays_overdue():
    assert effective_due("overdue", datetime.now() - timedelta(days=30)) == "overdue"


def test_custom_stays_custom_before_the_date():
    due_date = datetime.now() + timedelta(days=3)
    assert effective_due("custom", datetime.now(), due_date) == "custom"


def test_custom_becomes_overdue_after_the_date():
    due_date = datetime.now() - timedelta(hours=1)
    assert effective_due("custom", datetime.now() - timedelta(days=5), due_date) == "overdue"


def test_custom_without_a_date_does_not_crash():
    assert effective_due("custom", datetime.now(), None) == "custom"
