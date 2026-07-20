import flet as ft

from components import theme
from components.app_shell import shell_view


def _role_pie_chart(stats: dict) -> ft.PieChart:
    """Répartition des utilisateurs par rôle."""
    sections_data = [
        ("Étudiants", stats["total_students"], theme.Colors.PRIMARY_ACTION),
        ("Formateurs", stats["total_instructors"], theme.Colors.CERT),
        ("Admins", stats["total_users"] - stats["total_students"] - stats["total_instructors"],
         theme.Colors.PURPLE),
    ]
    total = sum(n for _, n, _ in sections_data) or 1
    sections = [
        ft.PieChartSection(
            value=n if n > 0 else 0.0001,  # évite une section à 0 invisible/erreur
            title=f"{round(n / total * 100)}%" if n > 0 else "",
            title_style=ft.TextStyle(size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
            color=color,
            radius=70,
        )
        for _, n, color in sections_data
    ]
    return ft.PieChart(
        sections=sections,
        sections_space=2,
        center_space_radius=36,
        expand=True,
    )


def _legend_dot(label: str, color: str, value) -> ft.Row:
    return ft.Row(
        spacing=8,
        controls=[
            ft.Container(width=10, height=10, border_radius=5, bgcolor=color),
            ft.Text(f"{label}", size=12, color=theme.Colors.TEXT_MUTED, expand=True),
            ft.Text(str(value), size=12, weight=ft.FontWeight.BOLD, color=theme.Colors.TEXT),
        ],
    )


def build_overview_view(page: ft.Page) -> ft.View:
    """Vue d'ensemble ADMIN : KPIs globaux + graphiques + activité récente."""
    try:
        stats = page.db.get_platform_stats()
    except Exception:
        stats = {
            "total_courses": 0, "published_courses": 0, "total_users": 0,
            "total_students": 0, "total_instructors": 0, "total_enrollments": 0,
            "total_certificates": 0, "success_rate": 0.0,
        }
    try:
        top_courses = page.db.get_enrollments_per_course()
    except Exception:
        top_courses = []
    try:
        recent_users = page.db.get_recent_signups()
    except Exception:
        recent_users = []

    kpi_row = ft.ResponsiveRow(
        spacing=14,
        run_spacing=14,
        controls=[
            theme.stat_card(ft.Icons.GROUP, "Utilisateurs", stats["total_users"],
                            theme.Colors.PRIMARY_ACTION, col={"xs": 12, "sm": 6, "md": 3}),
            theme.stat_card(ft.Icons.AUTO_STORIES, "Cours publiés",
                            f"{stats['published_courses']}/{stats['total_courses']}",
                            theme.Colors.TEAL, col={"xs": 12, "sm": 6, "md": 3}),
            theme.stat_card(ft.Icons.HOW_TO_REG, "Inscriptions", stats["total_enrollments"],
                            theme.Colors.PURPLE, col={"xs": 12, "sm": 6, "md": 3}),
            theme.stat_card(ft.Icons.WORKSPACE_PREMIUM, "Certificats délivrés",
                            stats["total_certificates"], theme.Colors.CERT,
                            col={"xs": 12, "sm": 6, "md": 3}),
        ],
    )

    success_card = theme.card(
        content=ft.Row(
            spacing=16,
            controls=[
                theme.tinted_icon(ft.Icons.TRENDING_UP, theme.Colors.SUCCESS, box=52, size=26),
                ft.Column(
                    expand=True,
                    spacing=4,
                    controls=[
                        theme.subtitle("Taux de réussite global aux quiz"),
                        theme.progress_bar(stats["success_rate"], color=theme.Colors.SUCCESS),
                    ],
                ),
                ft.Text(f"{stats['success_rate']}%", size=20, weight=ft.FontWeight.BOLD,
                        color=theme.Colors.SUCCESS),
            ],
        ),
    )

    charts_row = ft.ResponsiveRow(
        spacing=16,
        run_spacing=16,
        controls=[
            ft.Container(
                col={"xs": 12, "md": 7},
                content=theme.card(
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            theme.section_title("Cours les plus suivis"),
                            ft.Container(
                                height=220,
                                content=theme.bar_chart(top_courses) if top_courses
                                else theme.body("Pas encore d'inscription.", muted=True),
                            ),
                        ],
                    ),
                ),
            ),
            ft.Container(
                col={"xs": 12, "md": 5},
                content=theme.card(
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            theme.section_title("Répartition des utilisateurs"),
                            ft.Container(height=170, content=_role_pie_chart(stats)),
                            ft.Column(
                                spacing=6,
                                controls=[
                                    _legend_dot("Étudiants", theme.Colors.PRIMARY_ACTION,
                                               stats["total_students"]),
                                    _legend_dot("Formateurs", theme.Colors.CERT,
                                               stats["total_instructors"]),
                                    _legend_dot("Admins", theme.Colors.PURPLE,
                                               stats["total_users"] - stats["total_students"]
                                               - stats["total_instructors"]),
                                ],
                            ),
                        ],
                    ),
                ),
            ),
        ],
    )

    def recent_user_row(p):
        role = p.get("role", "student")
        return ft.Row(
            spacing=12,
            controls=[
                ft.CircleAvatar(
                    content=ft.Text((p.get("full_name") or "?")[:1].upper(), size=13,
                                    weight=ft.FontWeight.BOLD),
                    radius=16,
                    bgcolor=theme.tint(theme.Colors.PRIMARY_ACTION, 0.9),
                    color=ft.Colors.WHITE,
                ),
                ft.Text(p.get("full_name", "Utilisateur"), size=13, expand=True,
                        color=theme.Colors.TEXT),
                theme.chip(role.capitalize(), theme.Colors.PRIMARY_ACTION
                          if role == "student" else theme.Colors.CERT),
            ],
        )

    recent_rows = [recent_user_row(p) for p in recent_users] if recent_users else [
        theme.body("Aucun utilisateur pour l'instant.", muted=True)
    ]
    recent_card = theme.card(
        content=ft.Column(
            spacing=12,
            controls=[theme.section_title("Derniers utilisateurs inscrits"), *recent_rows],
        ),
    )

    body = ft.Container(
        padding=ft.padding.symmetric(horizontal=24, vertical=20),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                theme.page_title("Vue d'ensemble"),
                theme.body("Activité globale de la plateforme.", muted=True),
                ft.Container(height=16),
                kpi_row,
                ft.Container(height=16),
                success_card,
                ft.Container(height=16),
                charts_row,
                ft.Container(height=16),
                recent_card,
                ft.Container(height=20),
            ],
        ),
    )

    return shell_view(page, title="Vue d'ensemble", body=body)
