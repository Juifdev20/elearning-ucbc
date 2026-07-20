-- ============================================================
-- WORKFLOW D'APPROBATION DES COURS
-- A exécuter dans Supabase (SQL Editor). Idempotent.
--
-- Nécessite sql/roles_admin.sql (fonction public.is_admin()) déjà exécuté.
--
-- Le formateur crée un cours en brouillon, le soumet pour validation ;
-- seul un administrateur peut l'approuver (publié) ou le rejeter.
-- `is_published` reste la colonne utilisée par le catalogue étudiant
-- (RLS "Cours visibles par tous") : un trigger la maintient en
-- permanence synchronisée avec `status`, quelle que soit la façon
-- dont la ligne est modifiée (appli ou SQL direct).
-- ============================================================

alter table public.courses add column if not exists status text not null default 'draft'
  check (status in ('draft', 'pending_review', 'published', 'rejected'));
alter table public.courses add column if not exists rejection_reason text;

-- Reprise des cours existants : ceux déjà publiés passent en 'published',
-- les autres restent en 'draft' (ils devront être soumis puis validés).
update public.courses set status = 'published' where is_published = true and status = 'draft';

-- ------------------------------------------------------------
-- `is_published` = simple reflet de status (source de vérité unique).
-- ------------------------------------------------------------
create or replace function public.sync_course_published_flag()
returns trigger
language plpgsql
as $$
begin
  new.is_published := (new.status = 'published');
  return new;
end;
$$;

drop trigger if exists sync_is_published on public.courses;
create trigger sync_is_published
  before insert or update on public.courses
  for each row execute procedure public.sync_course_published_flag();

-- ------------------------------------------------------------
-- Verrou du workflow : entrer en 'published' ou 'rejected' est réservé
-- aux administrateurs — à la création ET à la modification. Un
-- formateur peut librement passer en 'draft' / 'pending_review'
-- (soumission, ou retrait d'un cours publié).
-- ------------------------------------------------------------
create or replace function public.enforce_course_approval_workflow()
returns trigger
language plpgsql
security definer
as $$
begin
  if new.status in ('published', 'rejected') and not public.is_admin() then
    raise exception 'Seul un administrateur peut approuver ou rejeter un cours';
  end if;
  return new;
end;
$$;

drop trigger if exists protect_course_approval on public.courses;
create trigger protect_course_approval
  before insert or update on public.courses
  for each row execute procedure public.enforce_course_approval_workflow();

-- Vérification.
select id, title, status, is_published from public.courses order by created_at desc limit 10;
