-- ============================================================
-- COMPTES DE DÉMONSTRATION — apprenant / formateur / admin
-- A exécuter dans Supabase (SQL Editor). Idempotent.
--
-- Crée 3 comptes DÉJÀ CONFIRMÉS (aucun email envoyé) :
--   etudiant@ucbc-test.com   / Etudiant123!   (student)
--   formateur@ucbc-test.com  / Formateur123!  (instructor)
--   admin@ucbc-test.com      / Admin123!      (admin)
-- ============================================================

do $$
declare
  acc record;
  uid uuid;
begin
  for acc in
    select * from (values
      ('etudiant@.com',  'Etudiant123',  'Étudiant',       'student'),
      ('formateur@.com', 'Formateur123', 'Formateur',      'instructor'),
      ('admin@u.com',     'Admin123',     'Administrateur', 'admin')
    ) as t(email, pwd, full_name, wanted_role)
  loop
    select id into uid from auth.users where email = acc.email;

    if uid is null then
      uid := gen_random_uuid();

      -- Utilisateur confirmé. Les colonnes "token" sont mises à '' (chaîne
      -- vide) et non NULL : GoTrue plante à la connexion si elles sont NULL.
      insert into auth.users (
        instance_id, id, aud, role, email, encrypted_password,
        email_confirmed_at, raw_app_meta_data, raw_user_meta_data,
        created_at, updated_at,
        confirmation_token, recovery_token,
        email_change, email_change_token_new, email_change_token_current,
        phone_change, phone_change_token, reauthentication_token
      ) values (
        '00000000-0000-0000-0000-000000000000', uid, 'authenticated', 'authenticated',
        acc.email, crypt(acc.pwd, gen_salt('bf')),
        now(),
        '{"provider":"email","providers":["email"]}'::jsonb,
        jsonb_build_object('full_name', acc.full_name),
        now(), now(),
        '', '', '', '', '', '', '', ''
      );

      -- Identité "email" associée (obligatoire pour la connexion).
      insert into auth.identities (
        id, user_id, provider_id, identity_data, provider,
        last_sign_in_at, created_at, updated_at
      ) values (
        gen_random_uuid(), uid, uid::text,
        jsonb_build_object('sub', uid::text, 'email', acc.email, 'email_verified', true),
        'email', now(), now(), now()
      );
    end if;

    -- Le trigger handle_new_user a créé le profil (rôle student par défaut) ;
    -- on applique le rôle voulu.
    update public.profiles
    set role = acc.wanted_role, full_name = acc.full_name
    where id = uid;
  end loop;
end $$;

-- ------------------------------------------------------------
-- SÉCURITÉ : empêcher un étudiant de s'auto-promouvoir.
-- (La policy "Chacun modifie son propre profil" autorise l'update de la
--  ligne entière, colonne role comprise — on verrouille via un trigger.)
-- Les changements de rôle restent possibles : depuis le SQL Editor
-- (auth.uid() est null) ou par un formateur/admin.
-- ------------------------------------------------------------
create or replace function public.prevent_role_escalation()
returns trigger
language plpgsql
security definer
as $$
begin
  if new.role is distinct from old.role
     and auth.uid() is not null
     and not public.is_staff() then
    raise exception 'Modification du rôle non autorisée';
  end if;
  return new;
end;
$$;

drop trigger if exists protect_role_change on public.profiles;
create trigger protect_role_change
  before update on public.profiles
  for each row execute procedure public.prevent_role_escalation();

-- ------------------------------------------------------------
-- VÉRIFICATION : doit afficher les 3 comptes avec leur rôle.
-- ------------------------------------------------------------
select u.email, p.full_name, p.role,
       (u.email_confirmed_at is not null) as confirme
from auth.users u
join public.profiles p on p.id = u.id
where u.email in ('etudiant@.com', 'formateur@.com', 'admin@u.com')
order by p.role;
