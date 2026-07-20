# 🎓 PROMPT PROJET — Plateforme E-Learning Professionnelle
## À copier-coller intégralement dans Claude Code (VS Code)

---

## 1. CONTEXTE ET OBJECTIF

Construis une **plateforme e-learning complète, professionnelle et prête pour la production**, comparable à des plateformes comme Coursera ou Udemy mais simplifiée. L'application doit être utilisable immédiatement par un vrai apprenant, avec une expérience fluide, moderne et intuitive, même pour des utilisateurs non technophiles.

**Stack technique imposée (non négociable) :**
- **Frontend** : Flet (Python) — une seule base de code pour Web, Desktop (Windows/macOS/Linux) et Mobile (Android/iOS)
- **Backend / Base de données** : Supabase (PostgreSQL + Auth + Storage + Row Level Security)
- **Développement local** : PostgreSQL + pgAdmin4, avec un schéma strictement identique à celui de Supabase, pour développer et tester hors ligne avant chaque déploiement
- **Déploiement final** :
  - Base de données + Auth + Storage → **Supabase** (production)
  - Application (web) → **Render** (Web Service, build Flet en mode web)
  - Build desktop/mobile → généré via `flet build` pour distribution locale (apk/exe)

Le projet doit être livré avec une architecture propre, documentée, prête à démontrer devant un enseignant évaluateur exigeant une réalisation professionnelle et fonctionnelle de bout en bout.

---

## 2. DESIGN SYSTEM — IDENTITÉ VISUELLE PROFESSIONNELLE

Le design doit inspirer confiance, clarté et sérieux académique. Palette et style **imposés** :

### Palette de couleurs (symbolisant l'éducation et le savoir)
- **Bleu principal (marque, boutons, liens)** : `#1E3A8A` (bleu profond) et `#2563EB` (bleu vif pour les actions)
- **Bleu clair (fonds, accents)** : `#EFF6FF`, `#DBEAFE`
- **Accent succès / progression** : `#16A34A` (vert)
- **Accent certification / brevet** : `#F59E0B` (or/ambre — symbole de réussite)
- **Alerte / erreur** : `#DC2626`
- **Neutres** : `#111827` (texte principal), `#6B7280` (texte secondaire), `#F9FAFB` (fond général)

### Typographie
- Titres : gras, tailles hiérarchisées claires (28/22/18/16px)
- Corps de texte : lisible, interligne confortable, jamais en dessous de 13px
- Hiérarchie visuelle nette entre titres, sous-titres et texte courant

### Iconographie
- Utiliser une bibliothèque d'icônes cohérente et professionnelle (Material Icons via Flet `ft.Icons`)
- Icônes systématiques pour : cours (📖 `MENU_BOOK`), progression (📊 `TRENDING_UP`), quiz (📝 `QUIZ`), certificat (🏅 `WORKSPACE_PREMIUM`), profil (`PERSON`), accueil (`HOME`)

### Composants visuels
- Cartes avec coins arrondis (radius 12-16px), ombres légères et douces
- Boutons avec états clairs (normal / hover / disabled / loading)
- Barres de progression animées et colorées
- Champs de formulaire avec labels flottants, icônes préfixes, validation visuelle immédiate

### Responsive et navigation adaptative (IMPORTANT)
- **Sur mobile** : barre de navigation **en bas de l'écran** (bottom navigation bar), style WhatsApp/Instagram, avec 4 onglets : **Accueil**, **Mes cours**, **Progression**, **Profil**
- **Sur desktop/web large** : barre de navigation **latérale** (sidebar) avec les mêmes 4 sections, plus large et avec labels visibles
- Détecter la largeur d'écran (`page.width`) pour basculer automatiquement entre les deux modes de navigation
- Design fluide, jamais de contenu coupé ou mal aligné selon la taille d'écran

---

## 3. FONCTIONNALITÉS COMPLÈTES ATTENDUES

### 3.1 Authentification et gestion de compte
- Inscription (nom complet, email, mot de passe) avec validation des champs
- Connexion / déconnexion sécurisées via Supabase Auth
- Récupération de mot de passe oublié (email de réinitialisation)
- Gestion de rôles : **Étudiant**, **Formateur**, **Administrateur**
- Persistance de session (l'utilisateur reste connecté en rouvrant l'app)

### 3.2 Catalogue de cours
- Liste de tous les cours publiés, en grille adaptative (cartes)
- Filtrage par catégorie, barre de recherche par mot-clé
- Chaque carte affiche : image de couverture, titre, catégorie, courte description, barre de progression si déjà inscrit
- Page de détail d'un cours : description complète, formateur, liste des leçons, nombre d'apprenants inscrits

### 3.3 Contenu pédagogique
- Cours organisés en **leçons ordonnées** (chapitres)
- Chaque leçon peut contenir : texte formaté, lien vidéo (intégration lecteur), fichier PDF téléchargeable
- Navigation séquentielle entre leçons (bouton "Leçon suivante")
- Marquage "Terminé" par leçon, avec mise à jour immédiate de la progression globale du cours

### 3.4 Suivi de progression
- Barre de progression par cours (% de leçons terminées)
- Tableau de bord personnel listant tous les cours en cours, avec pourcentage d'avancement
- Historique complet (dates de début, dernière activité)

### 3.5 Évaluation et certification
- Quiz final à choix multiples pour chaque cours (plusieurs questions, plusieurs options par question, une seule bonne réponse)
- Calcul automatique du score en pourcentage
- Seuil de réussite configurable par cours (ex: 70%)
- Si réussite → génération automatique d'un **certificat PDF professionnel** (nom de l'apprenant, titre du cours, score, date, mise en page soignée avec bordure et sceau visuel)
- Si échec → message encourageant, possibilité de repasser le quiz
- Historique des tentatives conservé

### 3.6 Profil utilisateur
- Photo/avatar, nom, rôle, biographie courte
- Vue d'ensemble de la progression sur tous les cours
- Liste des certificats obtenus, avec possibilité de télécharger chaque PDF
- Statistiques personnelles (nombre de cours terminés, temps estimé investi)

### 3.7 Espace Formateur / Administrateur
- Création et édition de cours (titre, description, catégorie, image)
- Ajout/réorganisation des leçons d'un cours
- Création du quiz final (questions, options, bonne réponse, seuil de réussite)
- Vue des apprenants inscrits et de leur progression par cours

### 3.8 Notifications et retours utilisateur (bonus si le temps le permet)
- Messages de confirmation clairs après chaque action (inscription réussie, leçon complétée, quiz réussi)
- Gestion propre des erreurs réseau/API avec messages compréhensibles (jamais d'erreur technique brute affichée à l'utilisateur)

---

## 4. ARCHITECTURE TECHNIQUE DU PROJET

```
elearning-platform/
├── main.py                        # Point d'entrée, routing principal
├── config.py                      # Variables d'environnement (Supabase, mode local/prod)
├── requirements.txt
├── .env.example
├── README.md                      # Instructions complètes d'installation et déploiement
│
├── services/
│   ├── supabase_service.py        # Toutes les requêtes Supabase (auth, data)
│   ├── certificate_service.py     # Génération PDF des certificats
│   └── local_db_service.py        # Connexion PostgreSQL locale (dev/tests)
│
├── views/
│   ├── login_view.py
│   ├── signup_view.py
│   ├── dashboard_view.py          # Accueil + catalogue
│   ├── course_detail_view.py
│   ├── quiz_view.py
│   ├── profile_view.py
│   ├── progress_view.py           # Onglet "Progression"
│   └── admin/
│       ├── course_editor_view.py
│       └── quiz_editor_view.py
│
├── components/
│   ├── bottom_nav.py               # Navigation mobile (bas d'écran)
│   ├── side_nav.py                 # Navigation desktop (latérale)
│   ├── course_card.py
│   └── theme.py                    # Couleurs, styles centralisés (design system)
│
├── sql/
│   ├── schema.sql                  # Schéma complet (tables + RLS + données démo)
│   └── local_schema.sql            # Version identique pour PostgreSQL local
│
└── assets/
    ├── icons/
    └── images/
```

**Exigences de code :**
- Séparation stricte logique métier (services/) / interface (views/) / composants réutilisables (components/)
- Aucune clé API en dur dans le code — tout via variables d'environnement (`.env`)
- Gestion des erreurs à chaque appel réseau (try/except avec message utilisateur clair)
- Code commenté aux endroits clés, noms de variables explicites

---

## 5. SCHÉMA DE BASE DE DONNÉES (PostgreSQL / Supabase)

Utiliser ce schéma comme base (à enrichir si nécessaire pour les fonctionnalités formateur) :

- `profiles` (id, full_name, role, avatar_url, bio, created_at)
- `courses` (id, title, description, category, cover_image_url, instructor_id, is_published, created_at)
- `lessons` (id, course_id, title, content, video_url, file_url, position)
- `quizzes` (id, course_id, title, pass_score)
- `quiz_questions` (id, quiz_id, question, position)
- `quiz_options` (id, question_id, option_text, is_correct)
- `lesson_progress` (id, user_id, lesson_id, completed_at)
- `enrollments` (id, user_id, course_id, enrolled_at)
- `quiz_attempts` (id, user_id, quiz_id, score, passed, attempted_at)
- `certificates` (id, user_id, course_id, certificate_url, issued_at)

**Sécurité obligatoire (Row Level Security) :**
- Chaque utilisateur ne peut lire/modifier que ses propres données de progression, tentatives, certificats
- Les cours et leçons sont en lecture publique pour tout utilisateur authentifié
- Seuls les formateurs/admins peuvent créer ou modifier des cours, leçons et quiz
- Écrire les policies RLS correspondantes pour chaque table

---

## 6. ENVIRONNEMENT DE DÉVELOPPEMENT LOCAL

- Configurer une connexion **PostgreSQL locale** (via pgAdmin4) avec un schéma identique à `schema.sql`
- Créer un système de bascule d'environnement dans `config.py` : `ENV=local` (Postgres local) ou `ENV=production` (Supabase), lu depuis `.env`
- Documenter dans le `README.md` les étapes précises pour :
  1. Installer PostgreSQL + pgAdmin4
  2. Créer la base locale et exécuter `sql/local_schema.sql`
  3. Lancer l'app en mode local pour développer/tester sans dépendre d'internet
  4. Basculer vers Supabase pour la production

---

## 7. DÉPLOIEMENT EN PRODUCTION

1. **Supabase** : créer le projet, exécuter `sql/schema.sql`, récupérer `SUPABASE_URL` et `SUPABASE_KEY`, activer le Storage pour les certificats PDF
2. **Render** :
   - Créer un Web Service à partir du dépôt Git
   - Build command : installer les dépendances + `flet build web` (ou lancement via `flet run --web`)
   - Variables d'environnement configurées dans Render (SUPABASE_URL, SUPABASE_KEY)
   - Fournir l'URL publique finale de démonstration
3. **Build mobile/desktop** : générer via `flet build apk` (Android) et `flet build windows` (ou macos/linux selon la machine), fournir les fichiers d'installation dans le livrable final

---

## 8. LIVRABLES ATTENDUS DE CE PROJET

1. Code source complet, organisé selon l'architecture ci-dessus, sur un dépôt Git
2. Application déployée et accessible en ligne (lien Render fonctionnel)
3. Build installable (APK Android au minimum, exécutable desktop si possible)
4. `README.md` complet : installation locale, configuration Supabase, déploiement, identifiants de démonstration (ex: compte étudiant test)
5. Jeu de données de démonstration : au moins 3 cours complets avec leçons et quiz fonctionnels
6. Application testée de bout en bout : inscription → apprentissage → quiz → certificat → profil

---

## 9. CRITÈRES DE "PROJET TERMINÉ"

- ✅ Un nouvel utilisateur peut s'inscrire, se connecter, suivre un cours, passer le quiz et obtenir un certificat sans aucune erreur
- ✅ L'interface est fluide et cohérente sur mobile (navigation en bas) et desktop (navigation latérale)
- ✅ Aucune donnée sensible n'est exposée entre utilisateurs (RLS vérifié)
- ✅ L'application fonctionne en production sur l'URL Render, pas seulement en local
- ✅ Le design respecte strictement la charte bleue/professionnelle définie en section 2

---

**Construis ce projet maintenant, étape par étape, en commençant par l'architecture des dossiers, puis la couche base de données/services, puis les écrans un par un en respectant scrupuleusement le design system défini. Explique chaque choix technique important au fil de la construction.**
