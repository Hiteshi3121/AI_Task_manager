-- Ishita HQ — Full schema (run once on fresh database)

-- BUCKETS
create table buckets (
    id text primary key,
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

-- SUB-BUCKETS
create table sub_buckets (
    id text primary key,
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

-- PEOPLE
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

-- STUDENTS
create table students (
    id serial primary key,
    name text not null,
    current_project text,
    status text not null default 'not_started'
        check (status in ('not_started', 'in_progress', 'on_hold', 'completed', 'cancelled')),
    next_follow_up text,
    last_updated timestamptz default now()
);

-- TASKS (includes Phase 2/3 columns)
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
    due_date timestamptz,
    done boolean default false,
    created_at timestamptz default now(),
    completed_at timestamptz,
    calendar_event_id text,
    recurrence text check (recurrence in ('daily','weekly','monthly'))
);

create index idx_tasks_bucket on tasks(bucket_id);
create index idx_tasks_done on tasks(done);
create index idx_tasks_created on tasks(created_at);

-- DAILY REPORTS
create table daily_reports (
    id serial primary key,
    report_date date not null unique,
    tasks_completed int default 0,
    tasks_carried_over int default 0,
    tasks_by_bucket jsonb default '{}',
    brief_text text,
    created_at timestamptz default now()
);

create index idx_daily_reports_date on daily_reports(report_date);

-- OAUTH TOKENS (Google Calendar)
create table if not exists oauth_tokens (
    id          serial primary key,
    provider    text not null default 'google',
    user_label  text not null default 'primary',
    access_token  text not null,
    refresh_token text,
    token_expiry  timestamptz,
    created_at    timestamptz not null default now(),
    updated_at    timestamptz not null default now(),
    unique (provider, user_label)
);
