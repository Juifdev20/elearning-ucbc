-- ============================================================
-- DONNÉES DE DÉMONSTRATION — leçons + quiz pour les 3 cours
-- A exécuter dans Supabase (SQL Editor) APRÈS schema.sql.
-- Idempotent : n'insère rien si le cours a déjà des leçons/un quiz.
-- ============================================================

-- ------------------------------------------------------------
-- 1. LEÇONS
-- ------------------------------------------------------------

-- Cours : Bases de Python pour Débutants
insert into public.lessons (course_id, title, content, video_url, position)
select c.id, v.title, v.content, v.video_url, v.position
from public.courses c
cross join (values
  ('Installation et premier programme',
   'Dans cette leçon, vous installez Python depuis python.org et écrivez votre tout premier programme : print("Bonjour le monde !"). Vous découvrez aussi l''éditeur VS Code et le terminal.',
   'https://www.youtube.com/watch?v=rfscVS0vtbw', 0),
  ('Variables et types de données',
   'Les variables stockent des informations : nombres entiers (int), décimaux (float), textes (str) et booléens (bool). Vous apprenez à les créer, les afficher et les convertir avec int(), str() et float().',
   null, 1),
  ('Conditions et boucles',
   'Les structures if/elif/else permettent de prendre des décisions ; les boucles for et while permettent de répéter des instructions. Vous écrivez un petit jeu de devinette de nombre pour tout mettre en pratique.',
   null, 2)
) as v(title, content, video_url, position)
where c.title = 'Bases de Python pour Débutants'
  and not exists (select 1 from public.lessons l where l.course_id = c.id);

-- Cours : Gestion de Projet Agile
insert into public.lessons (course_id, title, content, video_url, position)
select c.id, v.title, v.content, v.video_url, v.position
from public.courses c
cross join (values
  ('Pourquoi l''agilité ?',
   'Le manifeste agile (2001) privilégie les individus, le logiciel fonctionnel, la collaboration avec le client et l''adaptation au changement. Vous comparez le cycle en V traditionnel et les approches itératives.',
   null, 0),
  ('Scrum : rôles, événements, artefacts',
   'Scrum organise le travail en sprints de 2 à 4 semaines. Vous découvrez les 3 rôles (Product Owner, Scrum Master, équipe de développement), les événements (daily, sprint review, rétrospective) et le product backlog.',
   null, 1),
  ('Kanban et amélioration continue',
   'Kanban visualise le flux de travail sur un tableau (À faire / En cours / Terminé) et limite le travail en cours (WIP). Vous apprenez à mesurer le lead time et à animer une rétrospective d''amélioration.',
   null, 2)
) as v(title, content, video_url, position)
where c.title = 'Gestion de Projet Agile'
  and not exists (select 1 from public.lessons l where l.course_id = c.id);

-- Cours : Introduction à l'Informatique de Gestion
insert into public.lessons (course_id, title, content, video_url, position)
select c.id, v.title, v.content, v.video_url, v.position
from public.courses c
cross join (values
  ('Le système d''information de l''entreprise',
   'Un système d''information (SI) collecte, stocke, traite et diffuse l''information. Vous identifiez ses composantes : matériel, logiciels, données, procédures et personnes, et son rôle dans la prise de décision.',
   null, 0),
  ('Bases de données et ERP',
   'Les bases de données relationnelles structurent les données de l''entreprise ; les ERP (Odoo, SAP…) intègrent les processus (ventes, achats, comptabilité, stocks) autour d''une base unique.',
   null, 1),
  ('Sécurité et gouvernance des données',
   'Sauvegardes, contrôle d''accès, RGPD : vous découvrez les bonnes pratiques pour protéger le patrimoine informationnel de l''entreprise et les responsabilités de chaque acteur.',
   null, 2)
) as v(title, content, video_url, position)
where c.title = 'Introduction à l''Informatique de Gestion'
  and not exists (select 1 from public.lessons l where l.course_id = c.id);

-- ------------------------------------------------------------
-- 2. QUIZ (un par cours, seuil 70 %)
-- ------------------------------------------------------------
insert into public.quizzes (course_id, title, pass_score)
select c.id, 'Évaluation finale', 70
from public.courses c
where c.title in ('Bases de Python pour Débutants',
                  'Gestion de Projet Agile',
                  'Introduction à l''Informatique de Gestion')
  and not exists (select 1 from public.quizzes q where q.course_id = c.id);

-- ------------------------------------------------------------
-- 3. QUESTIONS
-- ------------------------------------------------------------

-- Python
insert into public.quiz_questions (quiz_id, question, position)
select q.id, v.question, v.position
from public.quizzes q
join public.courses c on c.id = q.course_id
cross join (values
  ('Quelle fonction affiche du texte à l''écran en Python ?', 0),
  ('Quel type de donnée représente un nombre décimal ?', 1),
  ('Quel mot-clé permet de répéter un bloc tant qu''une condition est vraie ?', 2)
) as v(question, position)
where c.title = 'Bases de Python pour Débutants'
  and not exists (select 1 from public.quiz_questions qq where qq.quiz_id = q.id);

-- Agile
insert into public.quiz_questions (quiz_id, question, position)
select q.id, v.question, v.position
from public.quizzes q
join public.courses c on c.id = q.course_id
cross join (values
  ('Quelle est la durée typique d''un sprint Scrum ?', 0),
  ('Qui est responsable de la priorisation du product backlog ?', 1),
  ('Que limite la méthode Kanban ?', 2)
) as v(question, position)
where c.title = 'Gestion de Projet Agile'
  and not exists (select 1 from public.quiz_questions qq where qq.quiz_id = q.id);

-- Informatique de Gestion
insert into public.quiz_questions (quiz_id, question, position)
select q.id, v.question, v.position
from public.quizzes q
join public.courses c on c.id = q.course_id
cross join (values
  ('Que signifie le sigle SI ?', 0),
  ('Quel logiciel intègre ventes, achats et comptabilité autour d''une base unique ?', 1),
  ('Quel règlement européen encadre la protection des données personnelles ?', 2)
) as v(question, position)
where c.title = 'Introduction à l''Informatique de Gestion'
  and not exists (select 1 from public.quiz_questions qq where qq.quiz_id = q.id);

-- ------------------------------------------------------------
-- 4. OPTIONS (la bonne réponse est marquée true)
-- ------------------------------------------------------------
-- Astuce : on cible chaque question par son texte, et on n'insère
-- que si elle n'a pas encore d'options.

-- Python Q1
insert into public.quiz_options (question_id, option_text, is_correct)
select qq.id, v.option_text, v.is_correct
from public.quiz_questions qq
cross join (values ('print()', true), ('echo()', false), ('write()', false)) as v(option_text, is_correct)
where qq.question = 'Quelle fonction affiche du texte à l''écran en Python ?'
  and not exists (select 1 from public.quiz_options o where o.question_id = qq.id);

-- Python Q2
insert into public.quiz_options (question_id, option_text, is_correct)
select qq.id, v.option_text, v.is_correct
from public.quiz_questions qq
cross join (values ('float', true), ('int', false), ('str', false)) as v(option_text, is_correct)
where qq.question = 'Quel type de donnée représente un nombre décimal ?'
  and not exists (select 1 from public.quiz_options o where o.question_id = qq.id);

-- Python Q3
insert into public.quiz_options (question_id, option_text, is_correct)
select qq.id, v.option_text, v.is_correct
from public.quiz_questions qq
cross join (values ('while', true), ('repeat', false), ('loop', false)) as v(option_text, is_correct)
where qq.question = 'Quel mot-clé permet de répéter un bloc tant qu''une condition est vraie ?'
  and not exists (select 1 from public.quiz_options o where o.question_id = qq.id);

-- Agile Q1
insert into public.quiz_options (question_id, option_text, is_correct)
select qq.id, v.option_text, v.is_correct
from public.quiz_questions qq
cross join (values ('2 à 4 semaines', true), ('6 mois', false), ('1 an', false)) as v(option_text, is_correct)
where qq.question = 'Quelle est la durée typique d''un sprint Scrum ?'
  and not exists (select 1 from public.quiz_options o where o.question_id = qq.id);

-- Agile Q2
insert into public.quiz_options (question_id, option_text, is_correct)
select qq.id, v.option_text, v.is_correct
from public.quiz_questions qq
cross join (values ('Le Product Owner', true), ('Le Scrum Master', false), ('Le directeur technique', false)) as v(option_text, is_correct)
where qq.question = 'Qui est responsable de la priorisation du product backlog ?'
  and not exists (select 1 from public.quiz_options o where o.question_id = qq.id);

-- Agile Q3
insert into public.quiz_options (question_id, option_text, is_correct)
select qq.id, v.option_text, v.is_correct
from public.quiz_questions qq
cross join (values ('Le travail en cours (WIP)', true), ('Le nombre de développeurs', false), ('Le budget du projet', false)) as v(option_text, is_correct)
where qq.question = 'Que limite la méthode Kanban ?'
  and not exists (select 1 from public.quiz_options o where o.question_id = qq.id);

-- Info Gestion Q1
insert into public.quiz_options (question_id, option_text, is_correct)
select qq.id, v.option_text, v.is_correct
from public.quiz_questions qq
cross join (values ('Système d''Information', true), ('Serveur Internet', false), ('Service Informatique', false)) as v(option_text, is_correct)
where qq.question = 'Que signifie le sigle SI ?'
  and not exists (select 1 from public.quiz_options o where o.question_id = qq.id);

-- Info Gestion Q2
insert into public.quiz_options (question_id, option_text, is_correct)
select qq.id, v.option_text, v.is_correct
from public.quiz_questions qq
cross join (values ('Un ERP', true), ('Un antivirus', false), ('Un navigateur web', false)) as v(option_text, is_correct)
where qq.question = 'Quel logiciel intègre ventes, achats et comptabilité autour d''une base unique ?'
  and not exists (select 1 from public.quiz_options o where o.question_id = qq.id);

-- Info Gestion Q3
insert into public.quiz_options (question_id, option_text, is_correct)
select qq.id, v.option_text, v.is_correct
from public.quiz_questions qq
cross join (values ('Le RGPD', true), ('La CNIL', false), ('L''ISO 9001', false)) as v(option_text, is_correct)
where qq.question = 'Quel règlement européen encadre la protection des données personnelles ?'
  and not exists (select 1 from public.quiz_options o where o.question_id = qq.id);

-- ------------------------------------------------------------
-- Vérification rapide (facultatif) :
--   select c.title, count(distinct l.id) lecons, count(distinct qq.id) questions
--   from courses c
--   left join lessons l on l.course_id = c.id
--   left join quizzes q on q.course_id = c.id
--   left join quiz_questions qq on qq.quiz_id = q.id
--   group by c.title;
-- Attendu : 3 leçons et 3 questions par cours.
-- ============================================================
