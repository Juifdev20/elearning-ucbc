-- ============================================================
-- GESTION DES RÔLES PAR L'ADMINISTRATEUR
-- A exécuter dans Supabase (SQL Editor). Idempotent.
--
-- Permet à un compte "admin" de changer le rôle des utilisateurs
-- depuis l'application (page Espace formateur > Utilisateurs).
-- ============================================================

-- L'utilisateur courant est-il administrateur ?
create or replace function public.is_admin()
returns boolean
language sql
security definer
stable
as $$
  select exists (
    select 1 from public.profiles
    where id = auth.uid() and role = 'admin'
  );
$$;

-- Les admins peuvent modifier le profil de n'importe qui (dont le rôle).
drop policy if exists "Admin gere les profils" on public.profiles;
create policy "Admin gere les profils" on public.profiles
  for update using (public.is_admin()) with check (public.is_admin());

-- Resserre la protection anti-escalade : seuls les ADMINS (ou le SQL
-- Editor) peuvent changer un rôle — plus les formateurs.
create or replace function public.prevent_role_escalation()
returns trigger
language plpgsql
security definer
as $$
begin
  if new.role is distinct from old.role
     and auth.uid() is not null
     and not public.is_admin() then
    raise exception 'Modification du rôle non autorisée';
  end if;
  return new;
end;
$$;

drop trigger if exists protect_role_change on public.profiles;
create trigger protect_role_change
  before update on public.profiles
  for each row execute procedure public.prevent_role_escalation();

-- Vérification : la policy doit apparaître.
select policyname, cmd from pg_policies
where tablename = 'profiles' order by policyname;
