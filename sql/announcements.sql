-- ============================================================
-- ANNONCES DE LA PLATEFORME
-- A exécuter dans Supabase (SQL Editor). Idempotent.
--
-- Permet à un formateur/admin de diffuser une annonce visible par
-- tous les utilisateurs connectés (affichée dans la cloche 🔔).
-- ============================================================

create table if not exists public.announcements (
  id uuid default uuid_generate_v4() primary key,
  title text not null,
  message text not null,
  created_by uuid references public.profiles(id) on delete set null,
  created_at timestamptz default now()
);

alter table public.announcements enable row level security;

-- Tout utilisateur connecté peut lire les annonces.
drop policy if exists "Annonces visibles par tous" on public.announcements;
create policy "Annonces visibles par tous" on public.announcements
  for select using (true);

-- Seul le staff (formateur/admin) peut créer ou supprimer des annonces.
drop policy if exists "Staff cree des annonces" on public.announcements;
create policy "Staff cree des annonces" on public.announcements
  for insert with check (public.is_staff());

drop policy if exists "Staff supprime des annonces" on public.announcements;
create policy "Staff supprime des annonces" on public.announcements
  for delete using (public.is_staff());

-- Vérification.
select count(*) as annonces_existantes from public.announcements;
