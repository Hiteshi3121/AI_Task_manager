### 1. AI task capture
Type anything in plain language into the capture bar and it's automatically
classified into:
- one of 7 buckets (Udukku, Ascend Now Social, Ascend Now Classes, My Music,
  My Social Media, Fitness, **Personal/Errands**)
- a sub-bucket, if it's a Udukku task (Music Room, Marketing, Operations,
  Partnerships, Content)
- the Udukku team member it's about, if one is named
- the student it's about, if one is named (matched against the live roster)
- a priority (high/medium/low)
- a due timing (today / this week / upcoming / no deadline)

**Note on the 7th bucket:** the original brief specifies six buckets. During
testing, generic personal errands (e.g. "buy milk") had nowhere correct to
go and were landing in Udukku by default. A 7th bucket, "Personal /
Errands," was added to fix this — flagging here since it's a scope change
from the original six, worth confirming you're happy with it.

### 2. Dashboard
- Seven bucket boards, each showing open tasks sorted by priority
  (high → medium → low), color-coded red/orange/green
- The Entrepreneurship Classes board also shows the live student roster
  (name, current project, next follow-up) regardless of whether that
  student has an open task right now
- ✓ to mark a task done, 🗑 to delete

### 3. Daily brief
- "What matters today": a number of bullets that scales with how busy the
  day actually is — a floor of 8 bullets, capped at 12, ordered high → low
  priority, each colored to match. Never invents a task that doesn't exist;
  if there are genuinely fewer than 8 open tasks, it shows exactly that many.
- "Who to check on today": people/students with an open high/medium
  priority task due today, this week, or overdue
- "Recent days": a rolling history of tasks completed vs. carried over

### 4. Backend / history
- Postgres stores everything; nothing is ever deleted except by explicit
  user action (the 🗑 button)
- `daily_reports` archives one row per day — tasks completed, carried over,
  and a breakdown by bucket — so trend analysis is possible later without
  re-modeling the data
- A `due` label like "today" doesn't silently go stale: if a task is left
  open past its window, it's automatically relabeled "overdue" the next
  time anyone loads the dashboard

## How to demo it

1. Start both servers (see [README.md](README.md) setup section).
2. Type a few tasks covering different buckets, e.g.:
   - "Follow up with Tanvi about music room attendance"
   - "Schedule next week's Instagram posts"
   - "Buy milk and pick up dry cleaning"
3. Watch them land in the correct boards within ~2 seconds, sorted by
   priority.
4. Click "Refresh" on the daily brief — see it reflect the new tasks.
5. Mark one done, delete another — confirm both disappear from the board
   immediately.

## Known limitations (being upfront, not hiding these)

- **Daily archive isn't a true cron job.** A background check runs hourly
  while the backend process is alive, which is enough for a dev machine
  left running, but a day could still be missed if the backend is fully
  off for an extended stretch around midnight. A real scheduled job is
  Phase 4 scope (once this is deployed to a server that's always on).
- **Frontend is one file.** `App.jsx` works fine at current scope but will
  need splitting into components before Phase 2's calendar UI and Phase 3's
  history browser land on top of it.
- **Test coverage is partial.** The deterministic logic (due-date staleness,
  brief bullet-count rules, LLM-output validation) has automated tests.
  The classifier and brief LLM calls themselves, and the DB-touching
  service functions, are verified manually each session, not by an
  automated suite yet.
- **No auth yet** — anyone with network access to the dev server can use
  it. This is explicitly Phase 4 scope.

## What changed during testing (for the record)

A live testing pass surfaced and fixed several issues before this was
called done:
- A missing database constraint let invalid `due` values slip through —
  added back, plus a defensive fallback in code.
- A malformed task ID crashed the API with a raw error — now returns a
  clean 400.
- `due` labels going stale over time (see above) — fixed with automatic
  recomputation.
- The daily brief always showed exactly 2–4 bullets regardless of how busy
  the day was — now scales 8–12 based on actual urgency.
- Bucket boards weren't sorted by priority — fixed.
- Daily brief bullets weren't color-coded by priority — fixed.