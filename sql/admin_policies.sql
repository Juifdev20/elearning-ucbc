-- ============================================================
-- POLICIES RLS — ESPACE FORMATEUR / ADMINISTRATEUR
-- A exécuter dans Supabase (SQL Editor) SUR UNE BASE OU schema.sql
-- a déjà été appliqué. Idempotent (drop if exists avant create).
--
-- Sans ces policies, les formateurs/admins ne peuvent PAS créer ou
-- modifier de cours/leçons/quiz (RLS bloque toute écriture par défaut).
-- ============================================================

-- Fonction utilitaire : l'utilisateur courant est-il formateur ou admin ?
-- SECURITY DEFINER pour éviter toute récursion RLS lors de la lecture de profiles.
create or replace function public.is_staff()
returns boolean
language sql
security definer
stable
as $$
  select exists (
    select 1 from public.profiles
    where id = auth.uid() and role in ('instructor', 'admin')
  );
$$;

-- ------------------------------------------------------------
-- COURS : le staff peut tout lire (y compris les brouillons non publiés)
-- et gérer (insert/update/delete).
-- ------------------------------------------------------------
drop policy if exists "Staff gere les cours" on public.courses;
create policy "Staff gere les cours" on public.courses
  for all using (public.is_staff()) with check (public.is_staff());

-- ------------------------------------------------------------
-- LEÇONS
-- ------------------------------------------------------------
drop policy if exists "Staff gere les lecons" on public.lessons;
create policy "Staff gere les lecons" on public.lessons
  for all using (public.is_staff()) with check (public.is_staff());

-- ------------------------------------------------------------
-- QUIZ + QUESTIONS + OPTIONS
-- ------------------------------------------------------------
drop policy if exists "Staff gere les quiz" on public.quizzes;
create policy "Staff gere les quiz" on public.quizzes
  for all using (public.is_staff()) with check (public.is_staff());

drop policy if exists "Staff gere les questions" on public.quiz_questions;
create policy "Staff gere les questions" on public.quiz_questions
  for all using (public.is_staff()) with check (public.is_staff());

drop policy if exists "Staff gere les options" on public.quiz_options;
create policy "Staff gere les options" on public.quiz_options
  for all using (public.is_staff()) with check (public.is_staff());

-- ------------------------------------------------------------
-- SUIVI DES APPRENANTS : le staff peut LIRE les inscriptions et la
-- progression de tous les apprenants (en plus des policies "propriétaire").
-- ------------------------------------------------------------
drop policy if exists "Staff voit toutes les inscriptions" on public.enrollments;
create policy "Staff voit toutes les inscriptions" on public.enrollments
  for select using (public.is_staff());

drop policy if exists "Staff voit toute la progression" on public.lesson_progress;
create policy "Staff voit toute la progression" on public.lesson_progress
  for select using (public.is_staff());

-- ------------------------------------------------------------
-- CERTIFICATS : le staff peut voir tous les certificats délivrés
-- (page "Certificats" admin/formateur). Sans cette policy, un
-- formateur/admin ne voit QUE ses propres certificats (RLS filtre
-- silencieusement les autres, sans erreur — bug difficile à repérer).
-- ------------------------------------------------------------
drop policy if exists "Staff voit tous les certificats" on public.certificates;
create policy "Staff voit tous les certificats" on public.certificates
  for select using (public.is_staff());

-- ============================================================
-- Pour promouvoir un compte en formateur (à faire une fois, par email) :
--   update public.profiles set role = 'instructor'
--   where id = (select id from auth.users where email = 'vous@exemple.com');
-- ============================================================
