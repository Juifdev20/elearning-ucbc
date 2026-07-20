import flet as ft

from services.supabase_service import db
from components import theme
from components.app_shell import shell_view

ROLES = [
    ("student", "Étudiant", None),        # couleur résolue à l'affichage
    ("instructor", "Formateur", None),
    ("admin", "Administrateur", None),
]


def _role_color(role: str) -> str:
    return {
        "student": theme.Colors.PRIMARY_ACTION,
        "instructor": theme.Colors.CERT,
        "admin": theme.Colors.PURPLE,
    }.get(role, theme.Colors.TEXT_MUTED)


def _role_label(role: str) -> str:
    return {"student": "Étudiant", "instructor": "Formateur",
            "admin": "Administrateur"}.get(role, role)


def build_users_view(page: ft.Page) -> ft.View:
    """Vue ADMIN : liste des utilisateurs et attribution des rôles."""
    try:
        profiles = db.get_all_profiles()
    except Exception:
        profiles = []

    my_id = db.current_user.id if db.current_user else None

    # Compteurs par rôle.
    counts = {"student": 0, "instructor": 0, "admin": 0}
    for p in profiles:
        r = p.get("role", "student")
        counts[r] = counts.get(r, 0) + 1

    stats = ft.ResponsiveRow(
        spacing=14,
        run_spacing=14,
        controls=[
            theme.stat_card(ft.Icons.SCHOOL, "Étudiants", counts.get("student", 0),
                            theme.Colors.PRIMARY_ACTION, col={"xs": 12, "sm": 4}),
            theme.stat_card(ft.Icons.CO_PRESENT, "Formateurs", counts.get("instructor", 0),
                            theme.Colors.CERT, col={"xs": 12, "sm": 4}),
            theme.stat_card(ft.Icons.ADMIN_PANEL_SETTINGS, "Administrateurs", counts.get("admin", 0),
                            theme.Colors.PURPLE, col={"xs": 12, "sm": 4}),
        ],
    )

    def change_role(profile):
        def handler(e):
            new_role = e.control.value
            try:
                updated = db.set_user_role(profile["id"], new_role)
                if updated:
                    page.open(ft.SnackBar(ft.Text(
                        f"✓ {profile.get('full_name', 'Utilisateur')} est maintenant "
                        f"{_role_label(new_role)}.")))
                    page.go("/admin/users")  # reconstruit (compteurs + chips à jour)
                else:
                    # RLS a filtré la mise à jour : policy manquante ou pas admin.
                    e.control.value = profile.get("role", "student")
                    page.open(ft.SnackBar(ft.Text(
                        "⚠️ Modification refusée. Avez-vous exécuté sql/roles_admin.sql ?")))
                    page.update()
            except Exception:
                e.control.value = profile.get("role", "student")
                page.open(ft.SnackBar(ft.Text("⚠️ Erreur lors du changement de rôle.")))
                page.update()
        return handler

    def user_row(profile):
        role = profile.get("role", "student")
        name = profile.get("full_name", "") or "Utilisateur"
        is_me = profile.get("id") == my_id

        role_dd = ft.Dropdown(
            value=role,
            width=190,
            dense=True,
            border_radius=theme.RADIUS_INPUT,
            border_color=theme.Colors.BORDER,
            disabled=is_me,  # on ne modifie pas son propre rôle (sécurité)
            tooltip="Vous ne pouvez pas modifier votre propre rôle" if is_me else "Attribuer un rôle",
            options=[ft.dropdown.Option(key=r, text=label) for r, label, _ in ROLES],
            on_change=change_role(profile),
        )

        return theme.card(
            padding=14,
            content=ft.Row(
                spacing=14,
                controls=[
                    ft.CircleAvatar(
                        content=ft.Text(name[:1].upper(), weight=ft.FontWeight.BOLD),
                        radius=20,
                        bgcolor=theme.tint(_role_color(role), 0.9),
                        color=ft.Colors.WHITE,
                    ),
                    ft.Column(
                        expand=True,
                        spacing=3,
                        controls=[
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Text(name, weight=ft.FontWeight.W_700, size=14,
                                            color=theme.Colors.TEXT),
                                    theme.chip("Vous", theme.Colors.SUCCESS) if is_me else ft.Container(),
                                ],
                            ),
                            theme.chip(_role_label(role), _role_color(role)),
                        ],
                    ),
                    role_dd,
                ],
            ),
        )

    rows = [user_row(p) for p in profiles] if profiles else [
        theme.body("Aucun utilisateur trouvé.", muted=True)
    ]

    body = ft.Container(
        padding=ft.padding.symmetric(horizontal=24, vertical=20),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                theme.page_title("Gestion des utilisateurs"),
                theme.body("Attribuez les rôles : étudiant, formateur ou administrateur.",
                           muted=True),
                ft.Container(height=16),
                stats,
                ft.Container(height=20),
                theme.section_title(f"Tous les utilisateurs ({len(profiles)})"),
                ft.Container(height=8),
                ft.Column(spacing=10, controls=rows),
                ft.Container(height=20),
            ],
        ),
    )

    return shell_view(page, title="Utilisateurs & rôles", body=body)
