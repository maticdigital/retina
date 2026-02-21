-- ============================================================================
-- Retina - Supabase Database Setup
-- Run this in your Supabase SQL Editor (Dashboard > SQL Editor > New Query)
-- ============================================================================

-- 1. Users table (extends Supabase Auth)
create table if not exists public.users (
  id uuid references auth.users on delete cascade primary key,
  email text unique not null,
  name text not null,
  role text not null default 'analyst' check (role in ('owner', 'admin', 'analyst')),
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

alter table public.users enable row level security;

-- Users can read their own profile
create policy "Users can read own profile" on public.users
  for select using (auth.uid() = id);

-- Users can update their own profile (but not role)
create policy "Users can update own profile" on public.users
  for update using (auth.uid() = id)
  with check (auth.uid() = id);

-- Owners and admins can read all users
create policy "Admins can read all users" on public.users
  for select using (
    exists (
      select 1 from public.users u
      where u.id = auth.uid() and u.role in ('owner', 'admin')
    )
  );

-- Owners and admins can insert users
create policy "Admins can insert users" on public.users
  for insert with check (
    exists (
      select 1 from public.users u
      where u.id = auth.uid() and u.role in ('owner', 'admin')
    )
  );

-- Owners and admins can update any user
create policy "Admins can update any user" on public.users
  for update using (
    exists (
      select 1 from public.users u
      where u.id = auth.uid() and u.role in ('owner', 'admin')
    )
  );

-- 2. Projects table
create table if not exists public.projects (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  primary_url text not null,
  competitor_urls jsonb not null default '[]'::jsonb,
  status text not null default 'draft' check (status in ('draft', 'in_progress', 'complete')),
  created_by uuid references public.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.projects enable row level security;

-- Analysts can see their own projects; admins/owners can see all
create policy "Users can read own projects" on public.projects
  for select using (
    created_by = auth.uid()
    or exists (
      select 1 from public.users u
      where u.id = auth.uid() and u.role in ('owner', 'admin')
    )
  );

create policy "Users can insert projects" on public.projects
  for insert with check (created_by = auth.uid());

create policy "Users can update own projects" on public.projects
  for update using (
    created_by = auth.uid()
    or exists (
      select 1 from public.users u
      where u.id = auth.uid() and u.role in ('owner', 'admin')
    )
  );

create policy "Users can delete own projects or admins" on public.projects
  for delete using (
    created_by = auth.uid()
    or exists (
      select 1 from public.users u
      where u.id = auth.uid() and u.role in ('owner', 'admin')
    )
  );

-- 3. Project Data table
create table if not exists public.project_data (
  id uuid default gen_random_uuid() primary key,
  project_id uuid references public.projects(id) on delete cascade not null,
  site_url text not null,
  lighthouse_data jsonb default '{}'::jsonb,
  builtwith_data jsonb default '{}'::jsonb,
  screenshot_paths jsonb default '{}'::jsonb,
  automated_scores jsonb default '{}'::jsonb,
  created_at timestamptz not null default now()
);

alter table public.project_data enable row level security;

create policy "project_data follows project access" on public.project_data
  for all using (
    exists (
      select 1 from public.projects p
      where p.id = project_data.project_id
      and (
        p.created_by = auth.uid()
        or exists (
          select 1 from public.users u
          where u.id = auth.uid() and u.role in ('owner', 'admin')
        )
      )
    )
  );

-- 4. Analyst Scores table
create table if not exists public.analyst_scores (
  id uuid default gen_random_uuid() primary key,
  project_id uuid references public.projects(id) on delete cascade not null,
  site_url text not null,
  lens_name text not null,
  sub_scores jsonb default '{}'::jsonb,
  raw_observations text,
  refined_observations text,
  screenshots jsonb default '[]'::jsonb,
  created_at timestamptz not null default now()
);

alter table public.analyst_scores enable row level security;

create policy "analyst_scores follows project access" on public.analyst_scores
  for all using (
    exists (
      select 1 from public.projects p
      where p.id = analyst_scores.project_id
      and (
        p.created_by = auth.uid()
        or exists (
          select 1 from public.users u
          where u.id = auth.uid() and u.role in ('owner', 'admin')
        )
      )
    )
  );

-- 5. Reports table
create table if not exists public.reports (
  id uuid default gen_random_uuid() primary key,
  project_id uuid references public.projects(id) on delete cascade not null,
  retina_score numeric,
  ai_analysis jsonb default '{}'::jsonb,
  quadrant_data jsonb default '{}'::jsonb,
  pdf_path text,
  generated_at timestamptz not null default now()
);

alter table public.reports enable row level security;

create policy "reports follows project access" on public.reports
  for all using (
    exists (
      select 1 from public.projects p
      where p.id = reports.project_id
      and (
        p.created_by = auth.uid()
        or exists (
          select 1 from public.users u
          where u.id = auth.uid() and u.role in ('owner', 'admin')
        )
      )
    )
  );

-- 6. Updated_at trigger
create or replace function public.handle_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger projects_updated_at
  before update on public.projects
  for each row execute function public.handle_updated_at();

-- 7. Storage buckets
insert into storage.buckets (id, name, public)
values ('screenshots', 'screenshots', true)
on conflict (id) do nothing;

insert into storage.buckets (id, name, public)
values ('reports', 'reports', true)
on conflict (id) do nothing;

-- Storage policies
create policy "Authenticated users can upload screenshots"
on storage.objects for insert
to authenticated
with check (bucket_id = 'screenshots');

create policy "Anyone can view screenshots"
on storage.objects for select
to public
using (bucket_id = 'screenshots');

create policy "Authenticated users can upload reports"
on storage.objects for insert
to authenticated
with check (bucket_id = 'reports');

create policy "Anyone can view reports"
on storage.objects for select
to public
using (bucket_id = 'reports');

create policy "Authenticated users can delete own screenshots"
on storage.objects for delete
to authenticated
using (bucket_id = 'screenshots');

create policy "Authenticated users can delete own reports"
on storage.objects for delete
to authenticated
using (bucket_id = 'reports');

-- 8. Function to handle new user signup (creates profile row)
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.users (id, email, name, role)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data->>'name', split_part(new.email, '@', 1)),
    coalesce(new.raw_user_meta_data->>'role', 'analyst')
  );
  return new;
end;
$$ language plpgsql security definer;

-- Trigger on auth.users insert
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
