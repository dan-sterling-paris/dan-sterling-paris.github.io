-- Tables for gym.html. Run once in the Supabase SQL editor.

create table gym_exercises (
  id bigint generated always as identity primary key,
  name text not null,
  created_at timestamptz not null default now()
);

-- Every save is a new row, so full history is kept.
create table gym_entries (
  id bigint generated always as identity primary key,
  exercise_id bigint not null references gym_exercises(id) on delete cascade,
  weight numeric,
  reps int,
  sets int,
  rating text check (rating in ('green', 'amber', 'red')),
  created_at timestamptz not null default now()
);

create index gym_entries_exercise_created on gym_entries (exercise_id, created_at desc);

-- Most recent entry per exercise (what the page shows).
create view gym_latest with (security_invoker = true) as
  select distinct on (exercise_id) *
  from gym_entries
  order by exercise_id, created_at desc;

alter table gym_exercises enable row level security;
alter table gym_entries enable row level security;
-- No "to" role: covers anon and signed-in visitors (calories.html signs in on the same origin).
create policy "full access" on gym_exercises for all using (true) with check (true);
create policy "full access" on gym_entries for all using (true) with check (true);
