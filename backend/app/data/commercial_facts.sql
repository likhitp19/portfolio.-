-- Run once in Supabase → SQL Editor, then restart the API.
-- Demo policies: anon can read/write this table. Tighten before a public prod launch.

create table if not exists public.commercial_facts (
  entity_type text not null,
  entity_key text not null,
  season_year integer not null,
  metric text not null,
  value_usd double precision,
  status text,
  confidence double precision,
  source_url text,
  source_title text,
  snippet text,
  retrieved_at timestamptz,
  frozen boolean default false,
  value_low double precision,
  value_high double precision,
  primary key (entity_type, entity_key, season_year, metric)
);

alter table public.commercial_facts enable row level security;

drop policy if exists commercial_facts_read on public.commercial_facts;
drop policy if exists commercial_facts_write on public.commercial_facts;
drop policy if exists commercial_facts_update on public.commercial_facts;

create policy commercial_facts_read
  on public.commercial_facts for select
  to anon, authenticated
  using (true);

create policy commercial_facts_write
  on public.commercial_facts for insert
  to anon, authenticated
  with check (true);

create policy commercial_facts_update
  on public.commercial_facts for update
  to anon, authenticated
  using (true)
  with check (true);

grant select, insert, update on public.commercial_facts to anon, authenticated;

notify pgrst, 'reload schema';
