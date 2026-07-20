-- ============================================================
-- CLASSEMENT DES APPRENANTS (gamification)
-- A exécuter dans Supabase (SQL Editor). Idempotent.
--
-- Fonction agrégée SECURITY DEFINER : ne renvoie QUE des compteurs
-- (nom, nb certificats, nb cours terminés, nb leçons terminées) —
-- aucune donnée personnelle sensible (email, contenu, etc.) n'est
-- exposée, donc appelable par n'importe quel utilisateur connecté.
-- ============================================================

create or replace function public.get_leaderboard(limit_n integer default 20)
returns table (
  user_id uuid,
  full_name text,
  certificates_count bigint,
  courses_completed bigint,
  lessons_completed bigint
)
language sql
security definer
stable
as $$
  with lesson_totals as (
    select course_id, count(*) as total_lessons
    from public.lessons
    group by course_id
  ),
  progress_per_course as (
    select lp.user_id, l.course_id, count(distinct lp.lesson_id) as done_lessons
    from public.lesson_progress lp
    join public.lessons l on l.id = lp.lesson_id
    group by lp.user_id, l.course_id
  ),
  completed as (
    select ppc.user_id, count(*) as courses_completed
    from progress_per_course ppc
    join lesson_totals lt on lt.course_id = ppc.course_id
    where lt.total_lessons > 0 and ppc.done_lessons >= lt.total_lessons
    group by ppc.user_id
  ),
  lessons_done as (
    select user_id, count(*) as lessons_completed
    from public.lesson_progress
    group by user_id
  ),
  certs as (
    select user_id, count(*) as certificates_count
    from public.certificates
    group by user_id
  )
  select
    p.id as user_id,
    p.full_name,
    coalesce(certs.certificates_count, 0) as certificates_count,
    coalesce(completed.courses_completed, 0) as courses_completed,
    coalesce(lessons_done.lessons_completed, 0) as lessons_completed
  from public.profiles p
  left join certs on certs.user_id = p.id
  left join completed on completed.user_id = p.id
  left join lessons_done on lessons_done.user_id = p.id
  where p.role = 'student'
  order by certificates_count desc, courses_completed desc, lessons_completed desc, p.full_name asc
  limit limit_n;
$$;

grant execute on function public.get_leaderboard(integer) to authenticated;

-- Vérification.
select * from public.get_leaderboard(5);
