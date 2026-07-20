import os

import flet as ft

from services.supabase_service import SupabaseService
from components import theme
from components.app_shell import is_desktop, shell_view, home_route
from components.loading import build_loading_view, build_error_view, loading_body
from views.landing_view import build_landing_view
from views.login_view import build_login_view
from views.signup_view import build_signup_view
from views.forgot_password_view import build_forgot_password_view
from views.dashboard_view import build_dashboard_view
from views.my_courses_view import build_my_courses_view
from views.progress_view import build_progress_view
from views.certificates_view import build_certificates_view
from views.leaderboard_view import build_leaderboard_view
from views.course_detail_view import build_course_detail_view
from views.lesson_view import build_lesson_view
from views.quiz_view import build_quiz_view
from views.profile_view import build_profile_view
from views.admin.overview_view import build_overview_view
from views.admin.instructor_overview_view import build_instructor_overview_view
from views.admin.my_students_view import build_my_students_view
from views.admin.my_certificates_view import build_my_certificates_view
from views.admin.pending_courses_view import build_pending_courses_view
from views.admin.admin_dashboard_view import build_admin_dashboard_view
from views.admin.course_editor_view import build_course_editor_view
from views.admin.quiz_editor_view import build_quiz_editor_view
from views.admin.learners_view import build_learners_view
from views.admin.users_view import build_users_view
from views.admin.certificates_view import build_certificates_view as build_admin_certificates_view
from views.admin.categories_view import build_categories_view
from views.admin.announcements_view import build_announcements_view


def main(page: ft.Page):
    # Une instance Supabase PAR SESSION : l'app est servie en web à plusieurs
    # utilisateurs en parallèle depuis le même process, une instance partagée
    # mélangerait les comptes connectés entre eux. Tout le code accède au
    # backend via `page.db`, jamais via un `db` importé globalement.
    page.db = SupabaseService()
    page.dark_mode = False  # préférence clair/sombre : propre à CETTE session
    page.title = "E-Learning UCBC"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = theme.app_theme()
    page.bgcolor = theme.Colors.BG
    page.padding = 0
    # Fenêtre desktop confortable par défaut (la sidebar s'affiche d'emblée).
    # Rétrécir la fenêtre sous 840px bascule automatiquement en mode mobile.
    page.window.width = 1200
    page.window.height = 800

    # Mémorise le mode d'affichage courant (mobile/desktop) pour ne reconstruire
    # la vue que lorsqu'on FRANCHIT le seuil responsive, pas à chaque pixel.
    state = {"desktop": is_desktop(page)}

    # Routes "instantanées" (aucune requête réseau à la construction) :
    # pas besoin d'afficher l'indicateur de chargement pour elles.
    INSTANT_ROUTES = {"/", "/login", "/signup", "/forgot-password"}

    # Les 4 sections principales accessibles par la sidebar / barre du bas :
    # pendant leur chargement on GARDE la coquille (menu + topbar) visible et
    # on n'affiche qu'un petit spinner dans la zone de contenu — pas de
    # loader plein écran (réservé aux boutons à l'intérieur des pages).
    SHELL_ROUTES = {
        "/dashboard": "Tableau de bord",
        "/my-courses": "Mes cours",
        "/progress": "Progression",
        "/certificates": "Mes certificats",
        "/leaderboard": "Classement",
        "/profile": "Mon profil",
        "/instructor": "Vue d'ensemble",
        "/instructor/students": "Mes apprenants",
        "/instructor/certificates": "Mes certificats",
        "/admin": "Vue d'ensemble",
        "/admin/courses": "Cours",
        "/admin/pending-courses": "Cours à valider",
        "/admin/users": "Utilisateurs & rôles",
        "/admin/certificates": "Certificats",
        "/admin/categories": "Catégories",
        "/admin/announcements": "Annonces",
    }

    def build_target_view():
        """Construit la vue correspondant à la route courante.

        Retourne None si une redirection a été déclenchée (garde d'auth).
        """
        if page.route == "/":
            # Page d'accueil publique (marketing). Un utilisateur déjà
            # connecté est redirigé directement vers son espace.
            if page.db.current_user:
                page.go(home_route(page))
                return None
            return build_landing_view(page)

        if page.route == "/signup":
            return build_signup_view(page)

        if page.route == "/forgot-password":
            return build_forgot_password_view(page)

        if page.route == "/dashboard":
            if not page.db.current_user:
                page.go("/login")
                return None
            return build_dashboard_view(page)

        if page.route == "/my-courses":
            if not page.db.current_user:
                page.go("/login")
                return None
            return build_my_courses_view(page)

        if page.route == "/progress":
            if not page.db.current_user:
                page.go("/login")
                return None
            return build_progress_view(page)

        if page.route.startswith("/course/"):
            if not page.db.current_user:
                page.go("/login")
                return None
            course_id = page.route.split("/course/")[1].split("/")[0]
            if page.route.endswith("/quiz"):
                return build_quiz_view(page, course_id)
            if "/lesson/" in page.route:
                try:
                    lesson_index = int(page.route.split("/lesson/")[1])
                except (ValueError, IndexError):
                    lesson_index = 0
                return build_lesson_view(page, course_id, lesson_index)
            return build_course_detail_view(page, course_id)

        if page.route == "/certificates":
            if not page.db.current_user:
                page.go("/login")
                return None
            return build_certificates_view(page)

        if page.route == "/leaderboard":
            if not page.db.current_user:
                page.go("/login")
                return None
            return build_leaderboard_view(page)

        if page.route == "/profile":
            if not page.db.current_user:
                page.go("/login")
                return None
            return build_profile_view(page)

        if page.route.startswith("/instructor"):
            # Espace réservé aux formateurs (l'admin a son propre "/admin").
            if not page.db.current_user:
                page.go("/login")
                return None
            if (page.db.current_profile or {}).get("role") != "instructor":
                page.go(home_route(page))
                return None
            if page.route == "/instructor/students":
                return build_my_students_view(page)
            if page.route == "/instructor/certificates":
                return build_my_certificates_view(page)
            return build_instructor_overview_view(page)

        if page.route.startswith("/admin"):
            # Espace réservé aux formateurs / administrateurs.
            if not page.db.current_user:
                page.go("/login")
                return None
            if not page.db.is_staff():
                page.go("/dashboard")
                return None

            # Pages réservées aux administrateurs (le formateur est renvoyé
            # vers sa page "Cours", sa véritable page d'accueil).
            ADMIN_ONLY_ROUTES = {
                "/admin", "/admin/users", "/admin/certificates",
                "/admin/categories", "/admin/announcements", "/admin/pending-courses",
            }
            if page.route in ADMIN_ONLY_ROUTES and not page.db.is_admin():
                page.go("/admin/courses")
                return None

            if page.route == "/admin":
                return build_overview_view(page)
            if page.route == "/admin/courses":
                return build_admin_dashboard_view(page)
            if page.route == "/admin/pending-courses":
                return build_pending_courses_view(page)
            if page.route == "/admin/users":
                return build_users_view(page)
            if page.route == "/admin/certificates":
                return build_admin_certificates_view(page)
            if page.route == "/admin/categories":
                return build_categories_view(page)
            if page.route == "/admin/announcements":
                return build_announcements_view(page)
            if page.route == "/admin/course/new":
                return build_course_editor_view(page, None)
            if page.route.startswith("/admin/course/"):
                admin_course_id = page.route.split("/admin/course/")[1].split("/")[0]
                if page.route.endswith("/quiz"):
                    return build_quiz_editor_view(page, admin_course_id)
                if page.route.endswith("/learners"):
                    return build_learners_view(page, admin_course_id)
                return build_course_editor_view(page, admin_course_id)
            # Route /admin/* non reconnue : repli sur la page d'accueil du rôle.
            return build_overview_view(page) if page.db.is_admin() else build_admin_dashboard_view(page)

        # "/login" par défaut
        return build_login_view(page)

    def route_change(route):
        # 1) RETOUR VISUEL IMMÉDIAT, adapté au type de navigation :
        #    - onglets sidebar/barre du bas -> la coquille reste, spinner
        #      uniquement dans la zone de contenu (l'onglet actif se met
        #      en surbrillance instantanément) ;
        #    - boutons à l'intérieur des pages (cours, leçon, quiz, admin)
        #      -> loader plein écran ;
        #    - routes instantanées (auth) -> aucun loader.
        if page.route in SHELL_ROUTES and page.db.current_user:
            title = SHELL_ROUTES[page.route]
            page.views.clear()
            page.views.append(shell_view(page, title, loading_body()))
            page.update()
        elif page.route not in INSTANT_ROUTES and page.route not in SHELL_ROUTES:
            page.views.clear()
            page.views.append(build_loading_view(page))
            page.update()

        # 2) Construction de la vraie vue (avec écran d'erreur + Réessayer
        #    si le réseau lâche pendant le chargement).
        try:
            target = build_target_view()
        except Exception:
            page.views.clear()
            page.views.append(build_error_view(page, on_retry=lambda: route_change(None)))
            page.update()
            return

        if target is None:  # redirection déclenchée par une garde d'auth
            return

        page.views.clear()
        page.views.append(target)
        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    def on_resized(e):
        # Reconstruit la vue courante uniquement quand on bascule
        # mobile <-> desktop, pour changer le mode de navigation.
        now_desktop = is_desktop(page)
        if now_desktop != state["desktop"]:
            state["desktop"] = now_desktop
            route_change(None)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    # NB : dans Flet 0.28 l'événement s'appelle bien "on_resized" (et non "on_resize").
    page.on_resized = on_resized
    # La topbar (refresh, dark mode, recherche, sidebar réductible) reconstruit
    # la vue courante via ce callback — stocké SUR la page (pas dans un état
    # partagé entre sessions) pour ne jamais rafraîchir le mauvais utilisateur.
    page.refresh_view = lambda: route_change(None)
    page.go(page.route)


if __name__ == "__main__":
    # Hébergement (Render...) : la plateforme impose son port via $PORT et
    # n'a pas de package `flet_desktop` — on sert directement en HTTP.
    # En local sans $PORT défini : comportement par défaut de `ft.app`.
    # upload_dir : dossier temporaire local requis par Flet pour recevoir les
    # fichiers (photo de profil) avant qu'on les transfère vers Supabase
    # Storage — voir services/supabase_service.py:upload_avatar().
    render_port = os.environ.get("PORT")
    if render_port:
        ft.app(target=main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0",
              port=int(render_port), upload_dir="uploads")
    else:
        ft.app(target=main, upload_dir="uploads")
