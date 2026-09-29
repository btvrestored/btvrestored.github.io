-- ============================================================================
-- BRIDGE TV — Firebase Realtime Database → Supabase (Postgres) schema
--
-- Mirrors database.rules.json:
--   admins   -> gate table, never directly readable/writable by clients
--   inbox    -> viewer moderation queue (anyone can submit a pending item,
--               only admins can list/update/delete; a viewer can check the
--               status of their own submission via get_inbox_status())
--   messages -> public on-air feed (anyone reads, only admins write)
--
-- Run this once in the Supabase SQL editor on a fresh project.
-- ============================================================================

create extension if not exists pgcrypto;

-- ----------------------------------------------------------------------------
-- ADMINS
-- Equivalent of Firebase's "admins": { ".read": false, ".write": false }.
-- No RLS policies are created for this table, so — aside from the
-- service_role key, which always bypasses RLS — nobody can read or write it
-- directly through the API. Add admins manually (see bottom of file).
-- ----------------------------------------------------------------------------
create table if not exists public.admins (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  created_at timestamptz not null default now()
);

alter table public.admins enable row level security;

create or replace function public.is_admin()
returns boolean
language sql
security definer
stable
set search_path = public
as $$
  select exists (select 1 from public.admins where user_id = auth.uid());
$$;

-- ----------------------------------------------------------------------------
-- INBOX — moderation queue (viewer submissions, pending/approved/rejected)
-- ----------------------------------------------------------------------------
create table if not exists public.inbox (
  id           uuid primary key default gen_random_uuid(),
  message      text not null check (char_length(message) > 0 and char_length(message) <= 200),
  user_name    text not null check (char_length(user_name) > 0 and char_length(user_name) <= 32),
  display_name text not null check (char_length(display_name) > 0 and char_length(display_name) <= 32),
  sms_type     text not null check (sms_type in ('normal','vip','glamour','express')),
  source       text not null default 'viewer' check (source = 'viewer'),
  sender_role  text not null default 'viewer' check (sender_role = 'viewer'),
  ts           bigint not null,                 -- Date.now() in ms, same as before
  approved     boolean not null default false,
  status       text not null default 'pending' check (status in ('pending','approved','rejected')),
  approved_at  bigint,
  rejected_at  bigint,
  created_at   timestamptz not null default now()
);

alter table public.inbox enable row level security;

-- Anyone (anonymous viewer) may submit a new pending request — mirrors the
-- Firebase ".write" validation on "inbox/$msgId" for non-admins.
create policy "viewers can submit a pending request"
  on public.inbox for insert
  to anon, authenticated
  with check (
    approved = false
    and status = 'pending'
    and source = 'viewer'
    and sender_role = 'viewer'
  );

-- Only admins can list/read the queue, update it (approve/reject) or delete
-- from it — mirrors ".read"/".write" on the parent "inbox" node.
create policy "admins can read inbox"
  on public.inbox for select
  to authenticated
  using (public.is_admin());

create policy "admins can update inbox"
  on public.inbox for update
  to authenticated
  using (public.is_admin())
  with check (public.is_admin());

create policy "admins can delete inbox"
  on public.inbox for delete
  to authenticated
  using (public.is_admin());

-- Status lookup for a single submitted request, without exposing the whole
-- queue to anonymous callers — mirrors Firebase's per-child ".read": true
-- while the parent "inbox" list stayed admin-only.
create or replace function public.get_inbox_status(request_id uuid)
returns table (id uuid, status text, approved boolean)
language sql
security definer
stable
set search_path = public
as $$
  select id, status, approved from public.inbox where id = request_id;
$$;

grant execute on function public.get_inbox_status(uuid) to anon, authenticated;

-- ----------------------------------------------------------------------------
-- MESSAGES — public on-air feed (what chat.html / the OBS widget displays)
-- ----------------------------------------------------------------------------
create table if not exists public.messages (
  id           uuid primary key default gen_random_uuid(),
  message      text not null check (char_length(message) > 0 and char_length(message) <= 200),
  user_name    text check (user_name is null or char_length(user_name) <= 32),
  display_name text check (display_name is null or char_length(display_name) <= 32),
  sms_type     text not null check (sms_type in ('normal','vip','glamour','express')),
  source       text check (source is null or source in ('viewer','moderator')),
  sender_role  text check (sender_role is null or sender_role in ('viewer','moderator')),
  ts           bigint not null,                 -- Date.now() in ms, same as before
  inbox_id     uuid references public.inbox(id) on delete set null,
  repeated     boolean not null default false,
  created_at   timestamptz not null default now()
);

alter table public.messages enable row level security;

-- Public on-air feed: anyone can read — mirrors "messages": { ".read": true }.
create policy "messages are publicly readable"
  on public.messages for select
  to anon, authenticated
  using (true);

-- Only admins (moderators) may push to or clear the on-air feed — mirrors
-- "messages": { ".write": "auth != null && ...admins... }.
create policy "only admins can insert messages"
  on public.messages for insert
  to authenticated
  with check (public.is_admin());

create policy "only admins can delete messages"
  on public.messages for delete
  to authenticated
  using (public.is_admin());

-- Helpful indexes for the admin log/inbox views and the public feed.
create index if not exists messages_ts_idx on public.messages (ts desc);
create index if not exists inbox_status_ts_idx on public.inbox (status, ts desc);

-- ----------------------------------------------------------------------------
-- REALTIME
-- Enable Postgres Changes so the admin panel (authenticated) and the public
-- feed (anonymous, messages table only — RLS still applies to each
-- subscriber) get live updates like the old db.ref(...).on('value') calls.
-- ----------------------------------------------------------------------------
alter publication supabase_realtime add table public.messages;
alter publication supabase_realtime add table public.inbox;

-- ----------------------------------------------------------------------------
-- Making yourself an admin (do this AFTER creating your user in
-- Authentication -> Users, e.g. with email+password matching the old
-- Firebase admin accounts):
--
--   insert into public.admins (user_id)
--   values ('paste-the-user-uuid-from-the-auth-users-table-here');
-- ----------------------------------------------------------------------------
