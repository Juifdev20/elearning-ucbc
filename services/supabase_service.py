"""
Couche d'accès à Supabase.
Toutes les requêtes de l'application passent par cette classe,
pour garder la logique métier séparée de l'interface (views/).
"""
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY


class SupabaseService:
    def __init__(self):
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.session = None
        self.current_user = None
        self.current_profile = None

    # ------------------------------------------------------------------
    # AUTHENTIFICATION
    # ------------------------------------------------------------------
    def sign_up(self, email: str, password: str, full_name: str):
        result = self.client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"full_name": full_name}},
        })
        return result

    def sign_in(self, email: str, password: str):
        result = self.client.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
        self.session = result.session
        self.current_user = result.user
        if self.current_user:
            self._load_profile()
        return result

    def sign_out(self):
        self.client.auth.sign_out()
        self.session = None
        self.current_user = None
        self.current_profile = None

    def reset_password(self, email: str):
        """Envoie un email de réinitialisation de mot de passe (Supabase Auth)."""
        return self.client.auth.reset_password_for_email(email)

    def _load_profile(self):
        res = (
            self.client.table("profiles")
            .select("*")
            .eq("id", self.current_user.id)
            .single()
            .execute()
        )
        self.current_profile = res.data

    # ------------------------------------------------------------------
    # COURS
    # ------------------------------------------------------------------
    def get_courses(self):
        res = self.client.table("courses").select("*").eq("is_published", True).execute()
        return res.data or []

    def get_course(self, course_id: str):
        res = self.client.table("courses").select("*").eq("id", course_id).single().execute()
        return res.data

    def get_lessons(self, course_id: str):
        res = (
            self.client.table("lessons")
            .select("*")
            .eq("course_id", course_id)
            .order("position")
            .execute()
        )
        return res.data or []

    # ------------------------------------------------------------------
    # INSCRIPTIONS ET PROGRESSION
    # ------------------------------------------------------------------
    def enroll(self, course_id: str):
        user_id = self.current_user.id
        existing = (
            self.client.table("enrollments")
            .select("id")
            .eq("user_id", user_id)
            .eq("course_id", course_id)
            .execute()
        )
        if existing.data:
            return existing.data[0]
        res = self.client.table("enrollments").insert({
            "user_id": user_id, "course_id": course_id
        }).execute()
        return res.data[0] if res.data else None

    def get_my_enrollments(self):
        user_id = self.current_user.id
        res = (
            self.client.table("enrollments")
            .select("*, courses(*)")
            .eq("user_id", user_id)
            .execute()
        )
        return res.data or []

    def mark_lesson_complete(self, lesson_id: str):
        user_id = self.current_user.id
        existing = (
            self.client.table("lesson_progress")
            .select("id")
            .eq("user_id", user_id)
            .eq("lesson_id", lesson_id)
            .execute()
        )
        if existing.data:
            return existing.data[0]
        res = self.client.table("lesson_progress").insert({
            "user_id": user_id, "lesson_id": lesson_id
        }).execute()
        return res.data[0] if res.data else None

    def get_course_progress(self, course_id: str) -> float:
        """Retourne le pourcentage de progression (0-100) pour un cours donné."""
        lessons = self.get_lessons(course_id)
        if not lessons:
            return 0.0
        user_id = self.current_user.id
        lesson_ids = [l["id"] for l in lessons]
        res = (
            self.client.table("lesson_progress")
            .select("lesson_id")
            .eq("user_id", user_id)
            .in_("lesson_id", lesson_ids)
            .execute()
        )
        completed = len(res.data or [])
        return round((completed / len(lessons)) * 100, 1)

    # ------------------------------------------------------------------
    # QUIZ
    # ------------------------------------------------------------------
    def get_quiz(self, course_id: str):
        res = (
            self.client.table("quizzes")
            .select("*, quiz_questions(*, quiz_options(*))")
            .eq("course_id", course_id)
            .single()
            .execute()
        )
        return res.data

    def submit_quiz_attempt(self, quiz_id: str, score: int, passed: bool):
        user_id = self.current_user.id
        res = self.client.table("quiz_attempts").insert({
            "user_id": user_id, "quiz_id": quiz_id, "score": score, "passed": passed
        }).execute()
        return res.data[0] if res.data else None

    def get_best_passed_score(self, course_id: str):
        """Meilleur score d'une tentative réussie pour le cours (ou None).

        Sert notamment à régénérer un certificat dont le fichier PDF local
        aurait disparu, en retrouvant le score d'origine.
        """
        quiz = (
            self.client.table("quizzes").select("id").eq("course_id", course_id).execute()
        )
        if not quiz.data:
            return None
        quiz_id = quiz.data[0]["id"]
        res = (
            self.client.table("quiz_attempts")
            .select("score")
            .eq("user_id", self.current_user.id)
            .eq("quiz_id", quiz_id)
            .eq("passed", True)
            .order("score", desc=True)
            .limit(1)
            .execute()
        )
        return res.data[0]["score"] if res.data else None

    # ------------------------------------------------------------------
    # CERTIFICATS
    # ------------------------------------------------------------------
    def create_certificate(self, course_id: str, certificate_url: str = None):
        user_id = self.current_user.id
        existing = (
            self.client.table("certificates")
            .select("id")
            .eq("user_id", user_id)
            .eq("course_id", course_id)
            .execute()
        )
        if existing.data:
            return existing.data[0]
        res = self.client.table("certificates").insert({
            "user_id": user_id, "course_id": course_id, "certificate_url": certificate_url
        }).execute()
        return res.data[0] if res.data else None

    def get_my_certificates(self):
        user_id = self.current_user.id
        res = (
            self.client.table("certificates")
            .select("*, courses(title)")
            .eq("user_id", user_id)
            .execute()
        )
        return res.data or []

    def get_my_activity_feed(self, limit: int = 30) -> list:
        """Historique chronologique des actions de l'utilisateur courant :
        inscriptions, leçons terminées, tentatives de quiz, certificats.
        """
        user_id = self.current_user.id
        events = []

        enrollments = (
            self.client.table("enrollments")
            .select("enrolled_at, courses(title)")
            .eq("user_id", user_id)
            .execute()
        )
        for en in (enrollments.data or []):
            events.append({
                "type": "enrollment",
                "date": en.get("enrolled_at"),
                "course_title": (en.get("courses") or {}).get("title", "Cours"),
            })

        lessons = (
            self.client.table("lesson_progress")
            .select("completed_at, lessons(title, courses(title))")
            .eq("user_id", user_id)
            .execute()
        )
        for lp in (lessons.data or []):
            lesson = lp.get("lessons") or {}
            events.append({
                "type": "lesson",
                "date": lp.get("completed_at"),
                "lesson_title": lesson.get("title", "Leçon"),
                "course_title": (lesson.get("courses") or {}).get("title", "Cours"),
            })

        attempts = (
            self.client.table("quiz_attempts")
            .select("attempted_at, score, passed, quizzes(courses(title))")
            .eq("user_id", user_id)
            .execute()
        )
        for at in (attempts.data or []):
            quiz = at.get("quizzes") or {}
            events.append({
                "type": "quiz",
                "date": at.get("attempted_at"),
                "score": at.get("score"),
                "passed": at.get("passed"),
                "course_title": (quiz.get("courses") or {}).get("title", "Cours"),
            })

        certs = (
            self.client.table("certificates")
            .select("issued_at, courses(title)")
            .eq("user_id", user_id)
            .execute()
        )
        for c in (certs.data or []):
            events.append({
                "type": "certificate",
                "date": c.get("issued_at"),
                "course_title": (c.get("courses") or {}).get("title", "Cours"),
            })

        events.sort(key=lambda e: e.get("date") or "", reverse=True)
        return events[:limit]

    # ------------------------------------------------------------------
    # CLASSEMENT (gamification, cf. sql/leaderboard.sql)
    # ------------------------------------------------------------------
    def get_leaderboard(self, limit_n: int = 20) -> list:
        res = self.client.rpc("get_leaderboard", {"limit_n": limit_n}).execute()
        return res.data or []

    # ------------------------------------------------------------------
    # ESPACE FORMATEUR / ADMINISTRATEUR
    # (les écritures nécessitent les policies RLS de sql/admin_policies.sql)
    # ------------------------------------------------------------------
    def is_staff(self) -> bool:
        """True si l'utilisateur courant est formateur ou administrateur."""
        role = (self.current_profile or {}).get("role", "student")
        return role in ("instructor", "admin")

    def is_admin(self) -> bool:
        """True si l'utilisateur courant est administrateur."""
        return (self.current_profile or {}).get("role") == "admin"

    # --- Gestion des utilisateurs (admin uniquement, cf. sql/roles_admin.sql) ---
    def get_all_profiles(self):
        """Tous les profils utilisateurs (lecture publique via RLS)."""
        res = (
            self.client.table("profiles")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return res.data or []

    def set_user_role(self, user_id: str, role: str):
        """Change le rôle d'un utilisateur. Nécessite d'être admin (RLS)."""
        if role not in ("student", "instructor", "admin"):
            raise ValueError(f"Rôle invalide : {role}")
        res = (
            self.client.table("profiles")
            .update({"role": role})
            .eq("id", user_id)
            .execute()
        )
        return res.data[0] if res.data else None

    # --- Cours ---
    def get_all_courses(self, mine_only: bool = False):
        """Tous les cours (publiés ou non) — réservé au staff pour l'édition.

        mine_only=True restreint aux cours créés par l'utilisateur courant
        (utilisé par l'interface formateur, qui ne doit gérer que ses cours).
        """
        query = self.client.table("courses").select("*").order("created_at", desc=True)
        if mine_only and self.current_user:
            query = query.eq("instructor_id", self.current_user.id)
        res = query.execute()
        return res.data or []

    def create_course(self, title, description, category, cover_image_url=None):
        """Crée un cours. Statut initial selon le rôle du créateur :
        - admin      -> 'published' (déjà l'autorité de validation)
        - formateur  -> 'draft' (doit être soumis puis validé par un admin)
        `is_published` est dérivé automatiquement de `status` par un trigger
        (cf. sql/course_approval.sql) : inutile de le préciser ici.
        """
        status = "published" if self.is_admin() else "draft"
        res = self.client.table("courses").insert({
            "title": title,
            "description": description,
            "category": category,
            "cover_image_url": cover_image_url,
            "instructor_id": self.current_user.id,
            "status": status,
        }).execute()
        return res.data[0] if res.data else None

    def update_course(self, course_id, fields: dict):
        res = self.client.table("courses").update(fields).eq("id", course_id).execute()
        return res.data[0] if res.data else None

    def delete_course(self, course_id):
        self.client.table("courses").delete().eq("id", course_id).execute()

    # --- Workflow d'approbation (cf. sql/course_approval.sql) ---
    def submit_course_for_review(self, course_id):
        """Le formateur soumet son cours (draft/rejected) pour validation admin."""
        res = (
            self.client.table("courses")
            .update({"status": "pending_review", "rejection_reason": None})
            .eq("id", course_id)
            .execute()
        )
        return res.data[0] if res.data else None

    def withdraw_course(self, course_id):
        """Le formateur retire un cours publié (repasse en brouillon)."""
        res = (
            self.client.table("courses")
            .update({"status": "draft"})
            .eq("id", course_id)
            .execute()
        )
        return res.data[0] if res.data else None

    def get_pending_courses(self):
        """Cours en attente de validation, avec leur formateur (admin uniquement)."""
        res = (
            self.client.table("courses")
            .select("*, profiles(full_name)")
            .eq("status", "pending_review")
            .order("created_at")
            .execute()
        )
        return res.data or []

    def approve_course(self, course_id):
        """Un administrateur approuve un cours en attente : publication immédiate."""
        res = (
            self.client.table("courses")
            .update({"status": "published", "rejection_reason": None})
            .eq("id", course_id)
            .execute()
        )
        return res.data[0] if res.data else None

    def reject_course(self, course_id, reason: str = ""):
        """Un administrateur rejette un cours en attente, avec motif optionnel."""
        res = (
            self.client.table("courses")
            .update({"status": "rejected", "rejection_reason": reason or None})
            .eq("id", course_id)
            .execute()
        )
        return res.data[0] if res.data else None

    # --- Leçons ---
    def create_lesson(self, course_id, title, content="", video_url=None, file_url=None, position=None):
        if position is None:
            existing = self.get_lessons(course_id)
            position = len(existing)
        res = self.client.table("lessons").insert({
            "course_id": course_id,
            "title": title,
            "content": content,
            "video_url": video_url,
            "file_url": file_url,
            "position": position,
        }).execute()
        return res.data[0] if res.data else None

    def update_lesson(self, lesson_id, fields: dict):
        res = self.client.table("lessons").update(fields).eq("id", lesson_id).execute()
        return res.data[0] if res.data else None

    def delete_lesson(self, lesson_id):
        self.client.table("lessons").delete().eq("id", lesson_id).execute()

    def swap_lesson_positions(self, lesson_a, lesson_b):
        """Échange les positions de deux leçons (réorganisation haut/bas)."""
        self.update_lesson(lesson_a["id"], {"position": lesson_b["position"]})
        self.update_lesson(lesson_b["id"], {"position": lesson_a["position"]})

    # --- Quiz ---
    def get_or_create_quiz(self, course_id, pass_score=70):
        existing = self.client.table("quizzes").select("*").eq("course_id", course_id).execute()
        if existing.data:
            return existing.data[0]
        res = self.client.table("quizzes").insert({
            "course_id": course_id, "pass_score": pass_score,
        }).execute()
        return res.data[0] if res.data else None

    def update_quiz(self, quiz_id, fields: dict):
        res = self.client.table("quizzes").update(fields).eq("id", quiz_id).execute()
        return res.data[0] if res.data else None

    def create_question(self, quiz_id, question, position=None):
        if position is None:
            existing = self.client.table("quiz_questions").select("id").eq("quiz_id", quiz_id).execute()
            position = len(existing.data or [])
        res = self.client.table("quiz_questions").insert({
            "quiz_id": quiz_id, "question": question, "position": position,
        }).execute()
        return res.data[0] if res.data else None

    def delete_question(self, question_id):
        self.client.table("quiz_questions").delete().eq("id", question_id).execute()

    def create_option(self, question_id, option_text, is_correct=False):
        res = self.client.table("quiz_options").insert({
            "question_id": question_id, "option_text": option_text, "is_correct": is_correct,
        }).execute()
        return res.data[0] if res.data else None

    # --- Suivi des apprenants ---
    def get_course_learners(self, course_id):
        """Liste des apprenants inscrits à un cours avec leur progression (%)."""
        enrollments = (
            self.client.table("enrollments")
            .select("user_id, enrolled_at, profiles(full_name)")
            .eq("course_id", course_id)
            .execute()
        )
        lessons = self.get_lessons(course_id)
        total = len(lessons)
        lesson_ids = [l["id"] for l in lessons]

        learners = []
        for en in (enrollments.data or []):
            uid = en["user_id"]
            progress = 0.0
            if total and lesson_ids:
                done = (
                    self.client.table("lesson_progress")
                    .select("lesson_id")
                    .eq("user_id", uid)
                    .in_("lesson_id", lesson_ids)
                    .execute()
                )
                progress = round((len(done.data or []) / total) * 100, 1)
            learners.append({
                "user_id": uid,
                "full_name": (en.get("profiles") or {}).get("full_name", "Apprenant"),
                "enrolled_at": en.get("enrolled_at"),
                "progress": progress,
            })
        return learners

    # ------------------------------------------------------------------
    # ANALYTICS (vue d'ensemble admin/formateur)
    # ------------------------------------------------------------------
    def get_platform_stats(self) -> dict:
        """KPIs globaux pour la vue d'ensemble administrateur."""
        courses = self.get_all_courses()
        profiles = self.get_all_profiles()
        enrollments = self.client.table("enrollments").select("id", count="exact").execute()
        certificates = self.client.table("certificates").select("id", count="exact").execute()
        attempts = self.client.table("quiz_attempts").select("passed").execute()

        attempts_data = attempts.data or []
        passed = sum(1 for a in attempts_data if a.get("passed"))
        success_rate = round((passed / len(attempts_data)) * 100, 1) if attempts_data else 0.0

        return {
            "total_courses": len(courses),
            "published_courses": sum(1 for c in courses if c.get("is_published", True)),
            "total_users": len(profiles),
            "total_students": sum(1 for p in profiles if p.get("role", "student") == "student"),
            "total_instructors": sum(1 for p in profiles if p.get("role") == "instructor"),
            "total_enrollments": enrollments.count or 0,
            "total_certificates": certificates.count or 0,
            "success_rate": success_rate,
        }

    def get_enrollments_per_course(self, top_n: int = 5) -> list:
        """Nombre d'inscriptions par cours, trié décroissant (pour le graphique)."""
        courses = self.get_all_courses()
        res = self.client.table("enrollments").select("course_id").execute()
        counts = {}
        for row in (res.data or []):
            cid = row["course_id"]
            counts[cid] = counts.get(cid, 0) + 1
        ranked = sorted(courses, key=lambda c: counts.get(c["id"], 0), reverse=True)
        return [
            {"title": c["title"], "count": counts.get(c["id"], 0)}
            for c in ranked[:top_n]
        ]

    def get_recent_signups(self, limit: int = 5) -> list:
        """Derniers utilisateurs inscrits sur la plateforme."""
        res = (
            self.client.table("profiles")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []

    # ------------------------------------------------------------------
    # CERTIFICATS (vue globale admin)
    # ------------------------------------------------------------------
    def get_all_certificates(self):
        """Tous les certificats délivrés, avec apprenant et cours."""
        res = (
            self.client.table("certificates")
            .select("*, profiles(full_name), courses(title)")
            .order("issued_at", desc=True)
            .execute()
        )
        return res.data or []

    # ------------------------------------------------------------------
    # ESPACE FORMATEUR : analyses, apprenants et certificats limités à
    # SES PROPRES cours (instructor_id = utilisateur courant).
    # ------------------------------------------------------------------
    def get_my_teaching_stats(self) -> dict:
        """KPIs de la Vue d'ensemble formateur, limités à ses propres cours."""
        my_courses = self.get_all_courses(mine_only=True)
        course_ids = [c["id"] for c in my_courses]

        if not course_ids:
            return {
                "total_courses": 0, "published_courses": 0,
                "total_students": 0, "total_certificates": 0, "avg_completion": 0.0,
            }

        enrollments = (
            self.client.table("enrollments").select("user_id, course_id")
            .in_("course_id", course_ids).execute()
        )
        enroll_data = enrollments.data or []
        distinct_students = {e["user_id"] for e in enroll_data}

        certificates = (
            self.client.table("certificates").select("id", count="exact")
            .in_("course_id", course_ids).execute()
        )

        # Moyenne des progressions individuelles sur tous les couples (cours, apprenant).
        progresses = []
        for cid in course_ids:
            lessons = self.get_lessons(cid)
            total = len(lessons)
            if not total:
                continue
            lesson_ids = [l["id"] for l in lessons]
            students_in_course = {e["user_id"] for e in enroll_data if e["course_id"] == cid}
            for uid in students_in_course:
                done = (
                    self.client.table("lesson_progress").select("lesson_id")
                    .eq("user_id", uid).in_("lesson_id", lesson_ids).execute()
                )
                progresses.append((len(done.data or []) / total) * 100)

        avg_completion = round(sum(progresses) / len(progresses), 1) if progresses else 0.0

        return {
            "total_courses": len(my_courses),
            "published_courses": sum(1 for c in my_courses if c.get("is_published", True)),
            "total_students": len(distinct_students),
            "total_certificates": certificates.count or 0,
            "avg_completion": avg_completion,
        }

    def get_enrollments_per_my_course(self, top_n: int = 5) -> list:
        """Nombre d'inscriptions par cours du formateur courant (pour le graphique)."""
        my_courses = self.get_all_courses(mine_only=True)
        course_ids = [c["id"] for c in my_courses]
        if not course_ids:
            return []
        res = self.client.table("enrollments").select("course_id").in_("course_id", course_ids).execute()
        counts = {}
        for row in (res.data or []):
            counts[row["course_id"]] = counts.get(row["course_id"], 0) + 1
        ranked = sorted(my_courses, key=lambda c: counts.get(c["id"], 0), reverse=True)
        return [{"title": c["title"], "count": counts.get(c["id"], 0)} for c in ranked[:top_n]]

    def get_my_students(self) -> list:
        """Apprenants inscrits à l'un des cours du formateur courant, avec
        progression (une ligne par couple apprenant/cours)."""
        my_courses = self.get_all_courses(mine_only=True)
        rows = []
        for course in my_courses:
            for learner in self.get_course_learners(course["id"]):
                rows.append({
                    "student_name": learner["full_name"],
                    "course_title": course["title"],
                    "progress": learner["progress"],
                    "enrolled_at": learner["enrolled_at"],
                })
        rows.sort(key=lambda r: r.get("enrolled_at") or "", reverse=True)
        return rows

    def get_my_issued_certificates(self):
        """Certificats délivrés pour les cours du formateur courant."""
        my_courses = self.get_all_courses(mine_only=True)
        course_ids = [c["id"] for c in my_courses]
        if not course_ids:
            return []
        res = (
            self.client.table("certificates")
            .select("*, profiles(full_name), courses(title)")
            .in_("course_id", course_ids)
            .order("issued_at", desc=True)
            .execute()
        )
        return res.data or []

    # ------------------------------------------------------------------
    # CATÉGORIES (dérivées des cours ; pas de table dédiée)
    # ------------------------------------------------------------------
    def get_categories_summary(self):
        """Catégories distinctes utilisées par les cours, avec leur nombre."""
        courses = self.get_all_courses()
        counts = {}
        for c in courses:
            cat = (c.get("category") or "").strip() or "Sans catégorie"
            counts[cat] = counts.get(cat, 0) + 1
        return sorted(
            [{"category": cat, "count": n} for cat, n in counts.items()],
            key=lambda x: x["category"].lower(),
        )

    def rename_category(self, old_category: str, new_category: str):
        """Renomme une catégorie sur tous les cours concernés (mise à jour groupée)."""
        res = (
            self.client.table("courses")
            .update({"category": new_category})
            .eq("category", old_category)
            .execute()
        )
        return len(res.data or [])

    # ------------------------------------------------------------------
    # ANNONCES (diffusées à tous les utilisateurs via la cloche de
    # notifications ; cf. sql/announcements.sql)
    # ------------------------------------------------------------------
    def get_announcements(self, limit: int = 10):
        res = (
            self.client.table("announcements")
            .select("*, profiles(full_name)")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []

    def create_announcement(self, title: str, message: str):
        res = self.client.table("announcements").insert({
            "title": title, "message": message, "created_by": self.current_user.id,
        }).execute()
        return res.data[0] if res.data else None

    def delete_announcement(self, announcement_id: str):
        self.client.table("announcements").delete().eq("id", announcement_id).execute()


# Instance unique partagée par toute l'application (pattern singleton simple)
db = SupabaseService()
