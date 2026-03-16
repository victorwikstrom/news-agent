-- Phase 4: Article scoring observability table
-- Run this in the Supabase SQL editor

create table article_scores (
  id uuid primary key default gen_random_uuid(),
  run_at timestamptz not null,
  article_url text not null,
  article_title text not null,
  source text not null,
  score_corroboration int,
  score_recency int,
  score_impact int,
  score_novelty int,
  score_authority int,
  score_total int,
  reasoning text,
  cluster_sources text[],
  selected boolean not null
);

-- Index for querying by run
create index idx_article_scores_run_at on article_scores (run_at desc);

-- Index for filtering selected articles
create index idx_article_scores_selected on article_scores (selected) where selected = true;
