-- TradesCenter domain schema draft.
-- Target: PostgreSQL/Supabase-style SQL with UUID keys.

create extension if not exists pgcrypto;

create table users (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  display_name text not null,
  role text not null check (role in ('homeowner', 'contractor', 'admin', 'support')),
  phone text,
  avatar_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table service_areas (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  province text,
  country_code char(2) not null default 'CA',
  postal_prefix text,
  latitude numeric(9,6),
  longitude numeric(9,6),
  created_at timestamptz not null default now(),
  unique (name, province, country_code)
);

create table trades (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  description text,
  icon_name text,
  created_at timestamptz not null default now()
);

create table homeowner_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null unique references users(id) on delete cascade,
  service_area_id uuid references service_areas(id) on delete set null,
  address_label text,
  project_preferences jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table contractor_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null unique references users(id) on delete cascade,
  company_name text not null,
  slug text not null unique,
  bio text,
  website_url text,
  logo_url text,
  cover_image_url text,
  years_in_business int check (years_in_business is null or years_in_business >= 0),
  verification_status text not null default 'unverified'
    check (verification_status in ('unverified', 'pending', 'verified', 'suspended', 'expired')),
  average_rating numeric(3,2) not null default 0 check (average_rating between 0 and 5),
  review_count int not null default 0 check (review_count >= 0),
  response_time_minutes int,
  response_rate numeric(5,2) not null default 0 check (response_rate between 0 and 100),
  profile_visibility text not null default 'public'
    check (profile_visibility in ('public', 'local', 'hidden')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table contractor_trades (
  contractor_id uuid not null references contractor_profiles(id) on delete cascade,
  trade_id uuid not null references trades(id) on delete restrict,
  is_primary boolean not null default false,
  created_at timestamptz not null default now(),
  primary key (contractor_id, trade_id)
);

create table contractor_service_areas (
  contractor_id uuid not null references contractor_profiles(id) on delete cascade,
  service_area_id uuid not null references service_areas(id) on delete restrict,
  radius_km numeric(6,2),
  created_at timestamptz not null default now(),
  primary key (contractor_id, service_area_id)
);

create table projects (
  id uuid primary key default gen_random_uuid(),
  contractor_id uuid references contractor_profiles(id) on delete set null,
  homeowner_id uuid references homeowner_profiles(id) on delete set null,
  trade_id uuid references trades(id) on delete set null,
  service_area_id uuid references service_areas(id) on delete set null,
  title text not null,
  description text,
  project_type text,
  status text not null default 'completed'
    check (status in ('requested', 'in_progress', 'completed', 'archived')),
  budget_min_cents bigint check (budget_min_cents is null or budget_min_cents >= 0),
  budget_max_cents bigint check (budget_max_cents is null or budget_max_cents >= 0),
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table project_media (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects(id) on delete cascade,
  media_url text not null,
  media_type text not null default 'image' check (media_type in ('image', 'video', 'document')),
  phase text check (phase in ('before', 'after', 'during', 'document')),
  caption text,
  alt_text text,
  sort_order int not null default 0,
  created_at timestamptz not null default now()
);

create table project_proof_items (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects(id) on delete cascade,
  proof_type text not null
    check (proof_type in ('license', 'insurance', 'inspection', 'review', 'timeline', 'photo', 'client_confirmation')),
  status text not null default 'pending'
    check (status in ('pending', 'approved', 'rejected', 'expired')),
  label text not null,
  document_url text,
  verified_by uuid references users(id) on delete set null,
  verified_at timestamptz,
  expires_at timestamptz,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table quote_requests (
  id uuid primary key default gen_random_uuid(),
  homeowner_id uuid not null references homeowner_profiles(id) on delete cascade,
  trade_id uuid references trades(id) on delete set null,
  service_area_id uuid references service_areas(id) on delete set null,
  title text not null,
  description text not null,
  timeline text,
  budget_min_cents bigint check (budget_min_cents is null or budget_min_cents >= 0),
  budget_max_cents bigint check (budget_max_cents is null or budget_max_cents >= 0),
  preferred_contact text check (preferred_contact in ('email', 'phone', 'sms', 'message')),
  status text not null default 'open'
    check (status in ('draft', 'open', 'matched', 'closed', 'cancelled')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table quote_request_media (
  id uuid primary key default gen_random_uuid(),
  quote_request_id uuid not null references quote_requests(id) on delete cascade,
  media_url text not null,
  media_type text not null default 'image' check (media_type in ('image', 'video', 'document')),
  caption text,
  created_at timestamptz not null default now()
);

create table quote_responses (
  id uuid primary key default gen_random_uuid(),
  quote_request_id uuid not null references quote_requests(id) on delete cascade,
  contractor_id uuid not null references contractor_profiles(id) on delete cascade,
  message text not null,
  estimate_min_cents bigint check (estimate_min_cents is null or estimate_min_cents >= 0),
  estimate_max_cents bigint check (estimate_max_cents is null or estimate_max_cents >= 0),
  status text not null default 'sent'
    check (status in ('sent', 'viewed', 'shortlisted', 'accepted', 'declined', 'withdrawn')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (quote_request_id, contractor_id)
);

create table conversations (
  id uuid primary key default gen_random_uuid(),
  quote_request_id uuid references quote_requests(id) on delete set null,
  subject text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table conversation_participants (
  conversation_id uuid not null references conversations(id) on delete cascade,
  user_id uuid not null references users(id) on delete cascade,
  last_read_at timestamptz,
  created_at timestamptz not null default now(),
  primary key (conversation_id, user_id)
);

create table messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references conversations(id) on delete cascade,
  sender_id uuid not null references users(id) on delete restrict,
  body text not null,
  created_at timestamptz not null default now()
);

create table reviews (
  id uuid primary key default gen_random_uuid(),
  homeowner_id uuid references homeowner_profiles(id) on delete set null,
  contractor_id uuid not null references contractor_profiles(id) on delete cascade,
  project_id uuid references projects(id) on delete set null,
  rating int not null check (rating between 1 and 5),
  title text,
  body text,
  moderation_status text not null default 'pending'
    check (moderation_status in ('pending', 'approved', 'rejected', 'hidden', 'flagged')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table verification_records (
  id uuid primary key default gen_random_uuid(),
  contractor_id uuid not null references contractor_profiles(id) on delete cascade,
  record_type text not null check (record_type in ('identity', 'license', 'insurance', 'business', 'project_proof')),
  status text not null default 'pending'
    check (status in ('pending', 'approved', 'rejected', 'expired')),
  reference_number text,
  document_url text,
  reviewed_by uuid references users(id) on delete set null,
  reviewed_at timestamptz,
  expires_at timestamptz,
  created_at timestamptz not null default now()
);

create table saved_contractors (
  homeowner_id uuid not null references homeowner_profiles(id) on delete cascade,
  contractor_id uuid not null references contractor_profiles(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (homeowner_id, contractor_id)
);

create table social_edges (
  id uuid primary key default gen_random_uuid(),
  actor_user_id uuid not null references users(id) on delete cascade,
  source_type text not null,
  source_id uuid not null,
  target_type text not null,
  target_id uuid not null,
  edge_type text not null
    check (edge_type in ('follows', 'saved', 'trusted', 'recommended', 'reviewed', 'commented', 'reacted', 'shared', 'verified', 'served', 'completed')),
  visibility text not null default 'public'
    check (visibility in ('public', 'local', 'followers', 'participant', 'admin')),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (actor_user_id, source_type, source_id, target_type, target_id, edge_type)
);

create table activity_events (
  id uuid primary key default gen_random_uuid(),
  actor_user_id uuid references users(id) on delete set null,
  verb text not null,
  object_type text not null,
  object_id uuid not null,
  target_type text,
  target_id uuid,
  trade_id uuid references trades(id) on delete set null,
  service_area_id uuid references service_areas(id) on delete set null,
  visibility text not null default 'public'
    check (visibility in ('public', 'local', 'followers', 'participant', 'admin')),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table social_feed_items (
  id uuid primary key default gen_random_uuid(),
  event_id uuid references activity_events(id) on delete cascade,
  actor_user_id uuid references users(id) on delete set null,
  verb text not null,
  object_type text not null,
  object_id uuid not null,
  target_type text,
  target_id uuid,
  trade_id uuid references trades(id) on delete set null,
  service_area_id uuid references service_areas(id) on delete set null,
  visibility text not null default 'public',
  rank_score numeric(10,4) not null default 0,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table graph_scores (
  id uuid primary key default gen_random_uuid(),
  target_type text not null,
  target_id uuid not null,
  service_area_id uuid references service_areas(id) on delete set null,
  trade_id uuid references trades(id) on delete set null,
  local_trust_score numeric(10,4) not null default 0,
  proof_strength_score numeric(10,4) not null default 0,
  recommendation_score numeric(10,4) not null default 0,
  response_quality_score numeric(10,4) not null default 0,
  profile_completeness_score numeric(10,4) not null default 0,
  network_proximity_score numeric(10,4) not null default 0,
  overall_rank_score numeric(10,4) not null default 0,
  calculated_at timestamptz not null default now(),
  unique (target_type, target_id, service_area_id, trade_id)
);

create index idx_contractor_trades_trade on contractor_trades(trade_id);
create index idx_contractor_service_areas_area on contractor_service_areas(service_area_id);
create index idx_projects_contractor on projects(contractor_id);
create index idx_projects_trade_area on projects(trade_id, service_area_id, created_at desc);
create index idx_project_media_project on project_media(project_id, sort_order);
create index idx_quote_requests_homeowner on quote_requests(homeowner_id, created_at desc);
create index idx_quote_requests_trade_area_status on quote_requests(trade_id, service_area_id, status, created_at desc);
create index idx_quote_responses_contractor on quote_responses(contractor_id, created_at desc);
create index idx_messages_conversation on messages(conversation_id, created_at);
create index idx_reviews_contractor_status on reviews(contractor_id, moderation_status, created_at desc);
create index idx_verification_contractor_status on verification_records(contractor_id, status, expires_at);
create index idx_social_edges_actor on social_edges(actor_user_id, edge_type, created_at desc);
create index idx_social_edges_target on social_edges(target_type, target_id, edge_type, created_at desc);
create index idx_activity_events_lookup on activity_events(verb, trade_id, service_area_id, created_at desc);
create index idx_social_feed_rank on social_feed_items(visibility, service_area_id, trade_id, rank_score desc, created_at desc);
create index idx_graph_scores_target on graph_scores(target_type, target_id);
create index idx_graph_scores_rank on graph_scores(service_area_id, trade_id, overall_rank_score desc);
