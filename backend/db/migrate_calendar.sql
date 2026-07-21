-- Run once to add calendar token storage.
-- Safe to re-run: uses IF NOT EXISTS.

create table if not exists oauth_tokens (
    id          serial primary key,
    provider    text not null default 'google',
    user_label  text not null default 'primary',  -- 'primary' = Ishita's account
    access_token  text not null,
    refresh_token text,
    token_expiry  timestamptz,
    created_at    timestamptz not null default now(),
    updated_at    timestamptz not null default now(),
    unique (provider, user_label)
);
