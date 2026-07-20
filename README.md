# 🎓 E-Learning UCBC — Plateforme d'apprentissage en ligne

Plateforme e-learning complète construite avec **Flet (Python)** et **Supabase**
(PostgreSQL + Auth + Row Level Security). Une seule base de code pour le
**web**, le **desktop** (Windows/macOS/Linux) et le **mobile** (Android/iOS).

## ✨ Fonctionnalités

**Côté apprenant**
- Inscription, connexion, mot de passe oublié (Supabase Auth)
- Catalogue de cours avec recherche et filtre par catégorie
- Leçons riches : texte, vidéo, support PDF, navigation séquentielle
- **Progression** : par cours et globale, avec **historique d'activité** chronologique
  (inscriptions, leçons terminées, tentatives de quiz, certificats)
- Quiz final par cours avec seuil de réussite configurable
- Certificat PDF généré automatiquement en cas de réussite
- **Mes certificats** : page dédiée, tous les brevets obtenus, téléchargeables
- **Classement** 🏆 : gamification — comparaison avec les autres apprenants
  (cours terminés, leçons, certificats), sans exposer de données personnelles

**Côté formateur** (rôle `instructor`) — interface dédiée, cantonnée à ses propres cours
- **Vue d'ensemble** : KPIs (cours publiés, apprenants, certificats délivrés),
  progression moyenne, graphique des inscriptions par cours
- **Mes cours** : création / édition / suppression — **workflow d'approbation** :
  un cours créé par un formateur naît en brouillon, doit être **soumis pour
  validation**, et seul un administrateur peut l'**approuver** (publication) ou
  le **rejeter** (avec motif). Un cours publié peut être retiré par son formateur.
- Gestion des leçons : ajout, édition, réorganisation, vidéo/PDF
- Éditeur de quiz : questions, options, bonne réponse, seuil
- **Mes apprenants** : tous les inscrits à ses cours, recherche, progression
- **Mes certificats** : certificats délivrés pour ses cours, recherche

**Côté administrateur** (rôle `admin`) — vue et contrôle globaux, interface dédiée
- **Vue d'ensemble** : KPIs de la plateforme, graphiques (cours les plus suivis,
  répartition des utilisateurs par rôle), taux de réussite global, derniers inscrits
- **Cours** : gestion de tous les cours (comme le formateur, sans restriction)
- **Utilisateurs & rôles** : attribution des rôles étudiant/formateur/admin
- **Cours à valider** : file d'attente des cours soumis par les formateurs
  (badge de notification dans la sidebar), approbation ou rejet avec motif
- **Certificats** : vue globale de tous les certificats délivrés, recherche, téléchargement
- **Catégories** : renommage groupé des catégories de cours
- **Annonces** : diffusion de messages à tous les utilisateurs (cloche 🔔)

**Expérience utilisateur**
- Design professionnel (charte bleue), **mode sombre** complet
- **Responsive** : sidebar latérale sur desktop, barre de navigation en bas
  sur mobile (bascule automatique à 840 px)
- Topbar : retour, actualiser, recherche globale, langue, notifications
- Indicateurs de chargement contextuels sur toutes les navigations

## 🗂 Structure du projet

```
elearning-app/
├── main.py                  # Point d'entrée + routeur (avec loader/erreur)
├── config.py                # Chargement du .env (SUPABASE_URL / KEY)
├── components/
│   ├── theme.py             # Design system : couleurs, dark mode, composants
│   ├── app_shell.py         # Sidebar desktop / bottom nav mobile + topbar
│   └── loading.py           # Écrans de chargement et d'erreur
├── services/
│   ├── supabase_service.py  # Toutes les requêtes (auth, cours, quiz, admin)
│   └── certificate_service.py  # Génération des certificats PDF (reportlab)
├── views/                   # Écrans apprenant (login, dashboard, cours…)
│   └── admin/               # Écrans formateur (éditeurs, apprenants)
└── sql/
    ├── schema.sql           # Schéma complet : tables + RLS + 3 cours démo
    ├── admin_policies.sql   # Policies formateur/admin (base existante)
    └── demo_data.sql        # Leçons + quiz de démonstration
```

## 🚀 Installation locale

### 1. Prérequis
- Python 3.11+ (testé avec 3.14)
- Un projet [Supabase](https://supabase.com) (gratuit)

### 2. Dépendances
```bash
python -m venv venv
venv\Scripts\activate        # Windows  (source venv/bin/activate sur Linux/macOS)
pip install -r requirements.txt
```

### 3. Base de données Supabase
Dans le dashboard Supabase → **SQL Editor**, exécutez dans cet ordre :

| Ordre | Fichier | Quand |
|---|---|---|
| 1 | `sql/schema.sql` | **Une seule fois**, sur un projet vierge (tables + sécurité + 3 cours) |
| 2 | `sql/admin_policies.sql` | Si votre base a été créée avant l'ajout de l'espace formateur (idempotent) |
| 3 | `sql/demo_data.sql` | Pour remplir les 3 cours avec leçons + quiz de démo (idempotent) |
| 4 | `sql/demo_accounts.sql` | Pour créer les 3 comptes de test pré-confirmés + protection anti-escalade de rôle (idempotent) |
| 5 | `sql/roles_admin.sql` | Pour permettre aux admins d'attribuer les rôles depuis l'application (idempotent) |
| 5bis | `sql/admin_policies.sql` *(mise à jour)* | **À ré-exécuter** : ajoute la lecture de tous les certificats pour le staff (page Certificats admin/formateur) — sans elle, seuls vos propres certificats sont visibles |
| 6 | `sql/announcements.sql` | Pour activer la page Annonces (table + policies, idempotent) |
| 7 | `sql/leaderboard.sql` | Pour activer la page Classement (fonction agrégée sécurisée, idempotent) |
| 8 | `sql/course_approval.sql` | Pour activer le workflow d'approbation des cours (colonnes + triggers, idempotent) |

### 4. Configuration
```bash
copy .env.example .env       # puis éditez .env
```
Renseignez `SUPABASE_URL` et `SUPABASE_KEY` (Project Settings → API).
⚠️ Utilisez la clé **anon au format JWT** (`eyJ...`) — les clés
`sb_publishable_...` sont refusées par supabase-py 2.9.1.

### 5. Comptes de démonstration

Après exécution de `sql/demo_accounts.sql`, trois comptes sont prêts :

| Rôle | Email | Mot de passe |
|---|---|---|
| 🎓 Apprenant | `etudiant@.com` | `Etudiant123` |
| 👨‍🏫 Formateur | `formateur@.com` | `Formateur123` |
| 🛡️ Administrateur | `admin@u.com` | `Admin123` |

### Attribution des rôles

Tout nouvel inscrit est **étudiant** par défaut. Pour changer un rôle :

- **Depuis l'application (recommandé)** : connectez-vous en **admin** →
  Espace formateur → icône 👥 **Utilisateurs & rôles** (en haut à droite) →
  choisissez le rôle dans la liste déroulante. Nécessite d'avoir exécuté
  `sql/roles_admin.sql`. Un admin ne peut pas modifier son propre rôle.
- **Via SQL Editor** (toujours possible) :
  ```sql
  update public.profiles set role = 'instructor'   -- ou 'admin'
  where id = (select id from auth.users where email = 'vous@exemple.com');
  ```

L'utilisateur doit se **reconnecter** pour que son nouveau rôle prenne effet
(le bouton « Espace formateur » apparaît alors dans la sidebar et le profil).

### 6. Lancer l'application
```bash
flet run                 # fenêtre desktop native
flet run --web           # dans le navigateur
```
Rétrécissez la fenêtre sous 840 px pour voir la navigation mobile.

## 🧪 Parcours de démonstration (bout en bout)

1. Créer un compte apprenant → connexion
2. Tableau de bord → choisir « Bases de Python pour Débutants »
3. Suivre les 3 leçons (« Marquer comme terminé ») → progression à 100 %
4. « Passer l'évaluation finale » → réussir le quiz (≥ 70 %)
5. Le certificat PDF est généré → onglet Profil → télécharger le brevet 🎓

## ☁️ Déploiement (production)

### Supabase (déjà en place)
La base, l'auth et la sécurité RLS sont hébergées chez Supabase.

### Render (application web)
1. Poussez le code sur un dépôt Git (GitHub)
2. Render → **New Web Service** → connectez le dépôt
3. Build command : `pip install -r requirements.txt`
4. Start command : `python main.py`
5. Variables d'environnement : `SUPABASE_URL`, `SUPABASE_KEY`

> ⚠️ Ne pas utiliser `flet run` en production : cet outil CLI est prévu pour le
> développement local (hot-reload) et importe un module optionnel
> (`flet_desktop`) absent des serveurs headless comme Render, ce qui fait
> planter le déploiement. `python main.py` appelle directement `ft.app(...)`,
> qui détecte automatiquement l'environnement serveur (Linux + `$PORT`) et
> sert l'app en HTTP sans dépendance desktop.

### Builds installables
```bash
flet build apk       # Android
flet build windows   # Exécutable Windows
```

## 🔐 Sécurité
- Aucune clé en dur : tout passe par `.env` (ignoré par Git)
- **Row Level Security** sur toutes les tables : chaque utilisateur ne voit
  que ses propres progressions, tentatives et certificats ; seuls les
  formateurs/admins peuvent modifier les contenus pédagogiques
- La clé `anon` est faite pour être embarquée côté client ; les droits
  réels sont contrôlés par les policies RLS côté serveur
