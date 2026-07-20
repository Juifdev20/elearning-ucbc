-- ============================================================
-- REPRISE DE COURS APRÈS 2 ÉCHECS CONSÉCUTIFS AU QUIZ
-- A exécuter dans Supabase (SQL Editor). Idempotent.
--
-- Nécessaire pour que reset_course_progress() (appelé automatiquement après
-- un 2e échec consécutif) puisse effacer la progression de l'apprenant sur
-- ce cours — sans cette policy, la suppression est bloquée silencieusement
-- par RLS (aucune policy DELETE n'existait sur lesson_progress).
-- ============================================================

drop policy if exists "Effacer sa propre progression" on public.lesson_progress;
create policy "Effacer sa propre progression"
on public.lesson_progress for delete
using (auth.uid() = user_id);

-- Vérification.
select policyname, cmd from pg_policies
where tablename = 'lesson_progress' order by cmd;
