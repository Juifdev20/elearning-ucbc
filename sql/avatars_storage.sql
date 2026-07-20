-- ============================================================
-- STOCKAGE DES PHOTOS DE PROFIL (avatars)
-- A exécuter dans Supabase (SQL Editor). Idempotent.
--
-- Bucket public en LECTURE (nécessaire pour afficher l'avatar dans
-- l'app ET sur le certificat PDF sans authentification), mais chaque
-- utilisateur ne peut écrire QUE dans son propre dossier
-- (avatars/<user_id>/avatar.xxx), grâce aux policies ci-dessous.
-- ============================================================

insert into storage.buckets (id, name, public)
values ('avatars', 'avatars', true)
on conflict (id) do nothing;

drop policy if exists "Avatars : chacun envoie sa propre photo" on storage.objects;
create policy "Avatars : chacun envoie sa propre photo"
on storage.objects for insert
with check (
  bucket_id = 'avatars'
  and (storage.foldername(name))[1] = auth.uid()::text
);

drop policy if exists "Avatars : chacun met à jour sa propre photo" on storage.objects;
create policy "Avatars : chacun met à jour sa propre photo"
on storage.objects for update
using (
  bucket_id = 'avatars'
  and (storage.foldername(name))[1] = auth.uid()::text
);

drop policy if exists "Avatars : chacun supprime sa propre photo" on storage.objects;
create policy "Avatars : chacun supprime sa propre photo"
on storage.objects for delete
using (
  bucket_id = 'avatars'
  and (storage.foldername(name))[1] = auth.uid()::text
);

-- Vérification.
select id, name, public from storage.buckets where id = 'avatars';
