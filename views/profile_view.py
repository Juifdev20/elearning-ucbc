import flet as ft

from services.supabase_service import db
from components import theme
from components.app_shell import shell_view


def build_profile_view(page: ft.Page) -> ft.View:
    """Onglet PROFIL : identité, statistiques et raccourcis vers les pages dédiées."""
    profile = db.current_profile or {}
    is_student = (profile.get("role", "student") or "student") == "student"

    enrollments, certificates = [], []
    if is_student:
        try:
            enrollments = db.get_my_enrollments()
        except Exception:
            enrollments = []
        try:
            certificates = db.get_my_certificates()
        except Exception:
            certificates = []

    def logout(e):
        db.sign_out()
        page.go("/login")

    full_name = profile.get("full_name", "") or "Apprenant"
    role = (profile.get("role", "student") or "student").capitalize()
    email = getattr(db.current_user, "email", "") or ""

    # ------------------------------------------------------------------
    # EN-TÊTE : bannière dégradée + avatar + identité
    # ------------------------------------------------------------------
    header = ft.Container(
        border_radius=20,
        gradient=theme.brand_gradient(),
        padding=24,
        content=ft.Row(
            spacing=18,
            controls=[
                ft.CircleAvatar(
                    content=ft.Text(full_name[:1].upper(), size=26, weight=ft.FontWeight.BOLD),
                    radius=34,
                    bgcolor=ft.Colors.WHITE,
                    color=theme.Colors.PRIMARY,
                ),
                ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text(full_name, size=20, weight=ft.FontWeight.BOLD,
                                color=ft.Colors.WHITE),
                        ft.Text(email, size=12,
                                color=ft.Colors.with_opacity(0.85, ft.Colors.WHITE)),
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=12, vertical=4),
                            border_radius=theme.RADIUS_BADGE,
                            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                            content=ft.Text(role, size=11, weight=ft.FontWeight.W_700,
                                            color=ft.Colors.WHITE),
                        ),
                    ],
                ),
            ],
        ),
    )

    completed = sum(
        1 for en in enrollments
        if db.get_course_progress((en.get("courses") or {}).get("id", "")) >= 100
    ) if is_student else 0

    body_controls = [header, ft.Container(height=16)]

    if is_student:
        # Statistiques rapides + raccourcis vers les pages dédiées (pas de
        # duplication du détail, déjà présent dans Progression/Certificats).
        stats = ft.ResponsiveRow(
            spacing=14,
            run_spacing=14,
            controls=[
                theme.stat_card(ft.Icons.MENU_BOOK, "Cours suivis", len(enrollments),
                                theme.Colors.PRIMARY_ACTION, col={"xs": 12, "sm": 4}),
                theme.stat_card(ft.Icons.CHECK_CIRCLE, "Terminés", completed,
                                theme.Colors.SUCCESS, col={"xs": 12, "sm": 4}),
                theme.stat_card(ft.Icons.WORKSPACE_PREMIUM, "Brevets", len(certificates),
                                theme.Colors.CERT, col={"xs": 12, "sm": 4}),
            ],
        )

        def shortcut_row(icon, color, label, sub, route):
            return theme.card(
                padding=14,
                on_click=lambda e: page.go(route),
                ink=True,
                content=ft.Row(
                    spacing=12,
                    controls=[
                        theme.tinted_icon(icon, color, box=40, size=20),
                        ft.Column(
                            expand=True, spacing=2,
                            controls=[
                                ft.Text(label, weight=ft.FontWeight.W_600, size=13,
                                        color=theme.Colors.TEXT),
                                ft.Text(sub, size=11, color=theme.Colors.TEXT_MUTED),
                            ],
                        ),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, color=theme.Colors.TEXT_MUTED),
                    ],
                ),
            )

        body_controls += [
            stats,
            ft.Container(height=20),
            shortcut_row(ft.Icons.TRENDING_UP, theme.Colors.PRIMARY_ACTION,
                        "Voir ma progression détaillée", "Par cours + historique d'activité",
                        "/progress"),
            ft.Container(height=10),
            shortcut_row(ft.Icons.WORKSPACE_PREMIUM, theme.Colors.CERT,
                        "Voir mes certificats", f"{len(certificates)} brevet(s) obtenu(s)",
                        "/certificates"),
            ft.Container(height=10),
            shortcut_row(ft.Icons.LEADERBOARD, theme.Colors.PURPLE,
                        "Voir le classement", "Comparez-vous aux autres apprenants",
                        "/leaderboard"),
            ft.Container(height=24),
        ]

    body_controls += [
        ft.OutlinedButton(
            "Se déconnecter",
            icon=ft.Icons.LOGOUT,
            on_click=logout,
            style=ft.ButtonStyle(color=theme.Colors.ERROR),
        ),
        ft.Container(height=20),
    ]

    body = ft.Container(
        padding=ft.padding.symmetric(horizontal=24, vertical=20),
        content=ft.Column(scroll=ft.ScrollMode.AUTO, controls=body_controls),
    )

    return shell_view(page, title="Mon profil", body=body)
