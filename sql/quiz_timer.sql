-- ============================================================
-- MINUTEUR D'ÉVALUATION (le formateur/admin fixe une durée en minutes)
-- A exécuter dans Supabase (SQL Editor). Idempotent.
-- ============================================================

alter table public.quizzes
  add column if not exists time_limit_minutes integer;

comment on column public.quizzes.time_limit_minutes is
  'Durée limite de l''évaluation en minutes. NULL = pas de limite de temps.';
