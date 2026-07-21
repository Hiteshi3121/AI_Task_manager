# Ishita HQ — Demo Script
**For: Ishita Parakh meeting**
**Prepared by: Hiteshi Aglawe**

---

## Overview (30 seconds)
"This is Ishita HQ — a personal command center built just for you. Everything Udukku, Ascend Now, your music, fitness, social, personal life — all in one place, powered by AI that knows your priorities."

---

## Demo Flow (~10 minutes)

### 1. Task Capture (2 min)
**Show the Today tab with 7 buckets.**

Type into the capture bar:
> "Call with Hiya tomorrow at 3pm to review the pitch deck"

- Watch it auto-classify into **Udukku**, **high priority**, due **this week**
- Point out the 📅 badge — it was added to Google Calendar automatically

Type a second task:
> "Post the Ascend Now reel we finished — publish Friday morning"

- Classifies into **Ascend Social**, medium priority

**Key message:** "You don't need to pick a bucket or priority. Just type it like you'd say it — the AI handles the sorting."

---

### 2. Voice Input (30 sec)
Click the 🎤 button and say:
> "Remind me to pay the gym membership this week"

- Shows it lands in **Fitness**, low priority, due this week

**Key message:** "Hands-free capture while you're on a call or between meetings."

---

### 3. Daily Brief (2 min)
Click **Brief** tab.

- Point out **What matters today** — AI-ranked by urgency
- Show **Today's calendar** — live pull from Google Calendar
- Show **Who to check on** — people mentioned across your tasks

**Key message:** "Every morning at 8 AM IST, this exact brief lands in your inbox — no login needed. You wake up knowing what needs attention."

---

### 4. Google Calendar Sync (1 min)
Open Google Calendar side by side (or show screenshot).

- Find the "Call with Hiya" event that was auto-created from step 1
- Show start time, duration, title — exactly as typed

If you delete the task from the board, offer to demo that the calendar event disappears too.

**Key message:** "It's not just a to-do list — your calendar stays in sync without you touching Google Calendar."

---

### 5. Recurring Tasks (1 min)
Show a recurring task card (or create one):
> "Post weekly Ascend Now update every Monday"

- Check the **weekly** recurrence dropdown on the card
- Mark it done — a fresh copy for next week auto-appears on the board

**Key message:** "Your weekly repeating work is never forgotten. Mark done, next one appears — zero admin."

---

### 6. Overdue Nudges (1 min)
Point to any task with a red background and **⚠️ 3d** badge.

- Explain: tasks open 3+ days get flagged
- These also appear in the daily brief email with a red section

**Key message:** "Nothing slips through the cracks. If something's been sitting for 3 days, it shows up visually and in your inbox."

---

### 7. History & Analytics (1 min)
Click **History** tab.

- Show KPI cards: completed this week, open tasks, total tasks
- Point to the bar chart — 30 days of activity
- Show bucket breakdown — where time is actually going

**Key message:** "At the end of any week or month, you can see exactly where your energy went — across all your projects."

---

### 8. People Tab (30 sec)
Click **People** tab.

- Show names extracted from tasks — Hiya, any collaborator mentioned
- Click a name to see all tasks involving them

**Key message:** "Collaboration threads stay attached to people, not just tasks."

---

### 9. Mobile / PWA (30 sec)
Open on phone or resize browser to mobile width.

- Show bottom navigation bar, capture bar at top
- Each section is thumb-friendly

"And it installs to your home screen like a native app — no App Store needed."

---

## Closing (30 sec)
"Everything here is built around how you actually work — not forcing you into a system. You type naturally, the AI categorizes, your calendar syncs, your brief arrives, and nothing falls through. I can customize any part of this — the buckets, the email timing, the briefing style — based on what you want."

---

## Quick Answers to Likely Questions

| Question | Answer |
|----------|--------|
| Can I add more buckets? | Yes — a 5-minute code change |
| What if Google Calendar goes down? | Tasks still work; calendar badge just won't appear |
| Who else can use it? | Currently it's single-user; multi-user (up to 6 separate dashboards) is the next phase |
| Where is the data stored? | PostgreSQL database, locally or cloud-hosted |
| Is this always on? | Yes — backend runs 24/7, email is sent automatically even if app is closed |
| Can I use voice for everything? | Yes — the mic button works on all modern browsers |
| How does the AI know priority? | Groq LLM reads the full task text and infers urgency + category |
