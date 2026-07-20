-- ============================================================
-- SCHEMA E-LEARNING PLATFORM - UCBC
-- A coller dans Supabase : SQL Editor > New query > Run
-- ============================================================

-- Extension pour générer des UUID
create extension if not exists "uuid-ossp";

-- ============================================================
-- 1. PROFILS UTILISATEURS (étend auth.users de Supabase)
-- ============================================================
create table public.profiles (
  id uuid references auth.users(id) on delete cascade primary key,
  full_name text not null,
  role text not null default 'student' check (role in ('student', 'instructor', 'admin')),
  avatar_url text,
  bio text,
  created_at timestamptz default now()
);

-- Création automatique du profil à l'inscription
create function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, full_name, role)
  values (new.id, coalesce(new.raw_user_meta_data->>'full_name', 'Nouvel utilisateur'), 'student');
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- ============================================================
-- 2. COURS
-- ============================================================
create table public.courses (
  id uuid default uuid_generate_v4() primary key,
  title text not null,
  description text,
  category text,
  cover_image_url text,
  instructor_id uuid references public.profiles(id),
  is_published boolean default true,
  created_at timestamptz default now()
);

-- ============================================================
-- 3. LEÇONS (chapitres d'un cours, ordonnés)
-- ============================================================
create table public.lessons (
  id uuid default uuid_generate_v4() primary key,
  course_id uuid references public.courses(id) on delete cascade not null,
  title text not null,
  content text,           -- contenu texte de la leçon
  video_url text,         -- optionnel : lien vidéo
  file_url text,          -- optionnel : PDF/support
  position integer not null default 0,  -- ordre d'affichage
  created_at timestamptz default now()
);

-- ============================================================
-- 4. QUIZ (un quiz final par cours)
-- ============================================================
create table public.quizzes (
  id uuid default uuid_generate_v4() primary key,
  course_id uuid references public.courses(id) on delete cascade not null,
  title text not null default 'Évaluation finale',
  pass_score integer not null default 70,  -- % requis pour réussir
  created_at timestamptz default now()
);

create table public.quiz_questions (
  id uuid default uuid_generate_v4() primary key,
  quiz_id uuid references public.quizzes(id) on delete cascade not null,
  question text not null,
  position integer not null default 0
);

create table public.quiz_options (
  id uuid default uuid_generate_v4() primary key,
  question_id uuid references public.quiz_questions(id) on delete cascade not null,
  option_text text not null,
  is_correct boolean not null default false
);

-- ============================================================
-- 5. PROGRESSION (leçons terminées par utilisateur)
-- ============================================================
create table public.lesson_progress (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  lesson_id uuid references public.lessons(id) on delete cascade not null,
  completed_at timestamptz default now(),
  unique(user_id, lesson_id)
);

-- Inscriptions aux cours
create table public.enrollments (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  course_id uuid references public.courses(id) on delete cascade not null,
  enrolled_at timestamptz default now(),
  unique(user_id, course_id)
);

-- ============================================================
-- 6. TENTATIVES DE QUIZ + CERTIFICATS
-- ============================================================
create table public.quiz_attempts (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  quiz_id uuid references public.quizzes(id) on delete cascade not null,
  score integer not null,
  passed boolean not null,
  attempted_at timestamptz default now()
);

create table public.certificates (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  course_id uuid references public.courses(id) on delete cascade not null,
  certificate_url text,
  issued_at timestamptz default now(),
  unique(user_id, course_id)
);

-- ============================================================
-- 7. SÉCURITÉ : ROW LEVEL SECURITY (RLS)
-- Chaque utilisateur ne voit / modifie que ses propres données
-- ============================================================
alter table public.profiles enable row level security;
alter table public.courses enable row level security;
alter table public.lessons enable row level security;
alter table public.quizzes enable row level security;
alter table public.quiz_questions enable row level security;
alter table public.quiz_options enable row level security;
alter table public.lesson_progress enable row level security;
alter table public.enrollments enable row level security;
alter table public.quiz_attempts enable row level security;
alter table public.certificates enable row level security;

-- Profils : chacun voit tous les profils publics, mais ne modifie que le sien
create policy "Profils visibles par tous" on public.profiles for select using (true);
create policy "Chacun modifie son propre profil" on public.profiles for update using (auth.uid() = id);

-- Cours et leçons : lecture publique (catalogue visible par tous les connectés)
create policy "Cours visibles par tous" on public.courses for select using (is_published = true);
create policy "Leçons visibles par tous" on public.lessons for select using (true);
create policy "Quiz visibles par tous" on public.quizzes for select using (true);
create policy "Questions visibles par tous" on public.quiz_questions for select using (true);
create policy "Options visibles par tous" on public.quiz_options for select using (true);

-- Progression : uniquement visible/modifiable par son propriétaire
create policy "Voir sa propre progression" on public.lesson_progress for select using (auth.uid() = user_id);
create policy "Ajouter sa propre progression" on public.lesson_progress for insert with check (auth.uid() = user_id);

-- Inscriptions : uniquement les siennes
create policy "Voir ses inscriptions" on public.enrollments for select using (auth.uid() = user_id);
create policy "S'inscrire soi-même" on public.enrollments for insert with check (auth.uid() = user_id);

-- Tentatives de quiz : uniquement les siennes
create policy "Voir ses tentatives" on public.quiz_attempts for select using (auth.uid() = user_id);
create policy "Créer ses tentatives" on public.quiz_attempts for insert with check (auth.uid() = user_id);

-- Certificats : uniquement les siens (données sensibles, protégées)
create policy "Voir ses certificats" on public.certificates for select using (auth.uid() = user_id);
create policy "Créer ses certificats" on public.certificates for insert with check (auth.uid() = user_id);

-- ============================================================
-- 7bis. POLICIES ESPACE FORMATEUR / ADMIN
-- (détaillé et idempotent dans sql/admin_policies.sql — inclus ici
--  pour qu'une installation neuve soit complète)
-- ============================================================
create or replace function public.is_staff()
returns boolean language sql security definer stable as $$
  select exists (
    select 1 from public.profiles
    where id = auth.uid() and role in ('instructor', 'admin')
  );
$$;

create policy "Staff gere les cours" on public.courses
  for all using (public.is_staff()) with check (public.is_staff());
create policy "Staff gere les lecons" on public.lessons
  for all using (public.is_staff()) with check (public.is_staff());
create policy "Staff gere les quiz" on public.quizzes
  for all using (public.is_staff()) with check (public.is_staff());
create policy "Staff gere les questions" on public.quiz_questions
  for all using (public.is_staff()) with check (public.is_staff());
create policy "Staff gere les options" on public.quiz_options
  for all using (public.is_staff()) with check (public.is_staff());
create policy "Staff voit toutes les inscriptions" on public.enrollments
  for select using (public.is_staff());
create policy "Staff voit toute la progression" on public.lesson_progress
  for select using (public.is_staff());

-- ============================================================
-- 8. DONNÉES DE DÉMONSTRATION (3 cours d'exemple)
-- ============================================================
insert into public.courses (title, description, category, is_published) values
('Introduction à l''Informatique de Gestion', 'Les fondamentaux des systèmes d''information en entreprise.', 'Informatique', true),
('Gestion de Projet Agile', 'Découvrez Scrum et Kanban pour piloter vos projets efficacement.', 'Management', true),
('Bases de Python pour Débutants', 'Apprenez à programmer en Python à partir de zéro.', 'Programmation', true);
