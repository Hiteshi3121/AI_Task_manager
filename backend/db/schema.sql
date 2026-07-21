-- Ishita HQ — Phase 1 schema
-- Run this once against your Postgres database to create all tables.

-- ============================================
-- BUCKETS (the 7 fixed top-level categories)
-- ============================================
create table buckets (
    id text primary key,              -- 'udukku', 'ascend_social', 'ascend_classes', 'music', 'social_brand', 'fitness', 'personal'
    name text not null,
    sort_order int not null
);

insert into buckets (id, name, sort_order) values
    ('udukku', 'Udukku', 1),
    ('ascend_social', 'Ascend Now — Social Media', 2),
    ('ascend_classes', 'Ascend Now — Entrepreneurship Classes', 3),
    ('music', 'My Music', 4),
    ('social_brand', 'My Social Media', 5),
    ('fitness', 'Fitness — Hyrox Prep', 6),
    ('personal', 'Personal / Errands', 7);

-- ============================================
-- SUB-BUCKETS (only Udukku has these in Phase 1)
-- ============================================
create table sub_buckets (
    id text primary key,              -- 'music_room', 'marketing', 'operations', 'partnerships', 'content'
    bucket_id text not null references buckets(id),
    name text not null,
    sort_order int not null
);

insert into sub_buckets (id, bucket_id, name, sort_order) values
    ('music_room', 'udukku', 'Music room', 1),
    ('marketing', 'udukku', 'Marketing', 2),
    ('operations', 'udukku', 'Operations', 3),
    ('partnerships', 'udukku', 'Partnerships', 4),
    ('content', 'udukku', 'Content', 5);

-- ============================================
-- PEOPLE (Udukku team members)
-- ============================================
create table people (
    id serial primary key,
    name text not null,
    role text,
    bucket_id text references buckets(id)
);

insert into people (name, role, bucket_id) values
    ('Evita', 'Operations Executive', 'udukku'),
    ('Meezan', 'Marketing & Content Intern', 'udukku'),
    ('Heeral', 'Graphics Intern', 'udukku'),
    ('Evani', 'Marketing Consultant & Projects', 'udukku'),
    ('Hiya', 'Video Editing', 'udukku'),
    ('Sagarika', 'Prompt Engineer — Tech', 'udukku'),
    ('Dhanya Sree', 'Prompt Engineer — Tech', 'udukku'),
    ('Tanvi', 'Music Room Facilitator', 'udukku');

-- ============================================
-- STUDENTS (roster for Ascend Now — Entrepreneurship Classes)
-- Standing record, independent of whether a task currently exists for them.
-- ============================================
create table students (
    id serial primary key,
    name text not null,
    current_project text,
    status text not null default 'not_started'
        check (status in ('not_started', 'in_progress', 'on_hold', 'completed', 'cancelled')),
    next_follow_up text,
    last_updated timestamptz default now()
);

-- ============================================
-- TASKS (the core table — every captured item lands here)
-- ============================================
create table tasks (
    id uuid primary key default gen_random_uuid(),
    raw_text text not null,
    title text not null,
    bucket_id text not null references buckets(id),
    sub_bucket_id text references sub_buckets(id),
    person_id int references people(id),
    student_id int references students(id),
    priority text not null check (priority in ('high','medium','low')),
    due text not null check (due in ('today','this week','upcoming','no deadline','overdue','custom')),
    due_date timestamptz,                   -- only set when due = 'custom'; an exact deadline
    done boolean default false,
    created_at timestamptz default now(),
    completed_at timestamptz
);

create index idx_tasks_bucket on tasks(bucket_id);
create index idx_tasks_done on tasks(done);
create index idx_tasks_created on tasks(created_at);

-- ============================================
-- DAILY REPORTS (one row per day — persistent history, never overwritten)
-- Structured fields so trend analysis is possible later without re-modeling.
-- ============================================
create table daily_reports (
    id serial primary key,
    report_date date not null unique,
    tasks_completed int default 0,
    tasks_carried_over int default 0,
    tasks_by_bucket jsonb default '{}',     -- e.g. {"udukku": 5, "music": 1}
    brief_text text,                         -- the "what matters today" narrative, archived
    created_at timestamptz default now()
);

create index idx_daily_reports_date on daily_reports(report_date);
