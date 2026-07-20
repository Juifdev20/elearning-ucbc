-- ============================================================
-- BLINDAGE : un certificat ne peut être émis que si TOUTES les
-- leçons du cours ont été marquées terminées par l'utilisateur.
-- A exécuter dans Supabase (SQL Editor). Idempotent.
--
-- Ceci complète la protection déjà faite côté application (Flet) :
-- même un appel direct à l'API Supabase (contournant l'app) sera
-- rejeté si l'utilisateur n'a pas fini le cours.
-- ============================================================

create or replace function public.enforce_certificate_completion()
returns trigger
language plpgsql
security definer
as $$
declare
  total_lessons integer;
  done_lessons integer;
begin
  select count(*) into total_lessons
  from public.lessons
  where course_id = new.course_id;

  -- Un cours sans leçon (contenu 100% quiz) est autorisé.
  if total_lessons = 0 then
    return new;
  end if;

  select count(distinct lp.lesson_id) into done_lessons
  from public.lesson_progress lp
  join public.lessons l on l.id = lp.lesson_id
  where lp.user_id = new.user_id
    and l.course_id = new.course_id;

  if done_lessons < total_lessons then
    raise exception 'Certificat refusé : le cours n''est pas terminé (% / % leçons).',
      done_lessons, total_lessons;
  end if;

  return new;
end;
$$;

drop trigger if exists trg_enforce_certificate_completion on public.certificates;

create trigger trg_enforce_certificate_completion
  before insert on public.certificates
  for each row
  execute function public.enforce_certificate_completion();

-- ============================================================
-- NETTOYAGE : supprime le(s) certificat(s) émis à tort avant
-- l'ajout de ce garde-fou (cours non terminé au moment de l'émission).
-- ============================================================
delete from public.certificates c
where exists (
  select 1
  from public.lessons l
  where l.course_id = c.course_id
) and (
  select count(distinct lp.lesson_id)
  from public.lesson_progress lp
  join public.lessons l on l.id = lp.lesson_id
  where lp.user_id = c.user_id and l.course_id = c.course_id
) < (
  select count(*) from public.lessons l where l.course_id = c.course_id
);

-- Vérification : ne doit plus rien renvoyer après le nettoyage ci-dessus.
select c.*
from public.certificates c
join public.lessons l on l.course_id = c.course_id
group by c.id
having count(distinct l.id) > (
  select count(distinct lp.lesson_id)
  from public.lesson_progress lp
  where lp.user_id = c.user_id
    and lp.lesson_id in (select id from public.lessons where course_id = c.course_id)
);
