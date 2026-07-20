import flet as ft

from components import theme
from components.app_shell import shell_view


def build_instructor_overview_view(page: ft.Page) -> ft.View:
    """Vue d'ensemble FORMATEUR : KPIs et graphique limités à ses propres cours."""
    try:
        stats = page.db.get_my_teaching_stats()
    except Exception:
        stats = {"total_courses": 0, "published_courses": 0, "total_students": 0,
                 "total_certificates": 0, "avg_completion": 0.0}
    try:
        top_courses = page.db.get_enrollments_per_my_course()
    except Exception:
        top_courses = []

    kpi_row = ft.ResponsiveRow(
        spacing=14,
        run_spacing=14,
        controls=[
            theme.stat_card(ft.Icons.AUTO_STORIES, "Mes cours",
                            f"{stats['published_courses']}/{stats['total_courses']} publiés",
                            theme.Colors.PRIMARY_ACTION, col={"xs": 12, "sm": 6, "md": 4}),
            theme.stat_card(ft.Icons.GROUP, "Apprenants", stats["total_students"],
                            theme.Colors.PURPLE, col={"xs": 12, "sm": 6, "md": 4}),
            theme.stat_card(ft.Icons.WORKSPACE_PREMIUM, "Certificats délivrés",
                            stats["total_certificates"], theme.Colors.CERT,
                            col={"xs": 12, "sm": 6, "md": 4}),
        ],
    )

    completion_card = theme.card(
        content=ft.Row(
            spacing=16,
            controls=[
                theme.tinted_icon(ft.Icons.TRENDING_UP, theme.Colors.SUCCESS, box=52, size=26),
                ft.Column(
                    expand=True,
                    spacing=4,
                    controls=[
                        theme.subtitle("Progression moyenne de vos apprenants"),
                        theme.progress_bar(stats["avg_completion"], color=theme.Colors.SUCCESS),
                    ],
                ),
                ft.Text(f"{stats['avg_completion']}%", size=20, weight=ft.FontWeight.BOLD,
                        color=theme.Colors.SUCCESS),
            ],
        ),
    )

    chart_card = theme.card(
        content=ft.Column(
            spacing=10,
            controls=[
                theme.section_title("Inscriptions par cours"),
                ft.Container(
                    height=220,
                    content=theme.bar_chart(top_courses) if top_courses
                    else theme.body("Pas encore d'inscription à l'un de vos cours.", muted=True),
                ),
            ],
        ),
    )

    no_course_hint = None
    if stats["total_courses"] == 0:
        no_course_hint = theme.card(
            padding=32,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    theme.tinted_icon(ft.Icons.ADD_BOX_OUTLINED, theme.Colors.PRIMARY_ACTION,
                                      box=64, size=32, radius=18),
                    theme.subtitle("Vous n'avez pas encore de cours"),
                    theme.body("Créez votre premier cours pour voir vos statistiques ici.",
                               muted=True),
                    ft.Container(height=4),
                    theme.primary_button(
                        "Créer un cours", icon=ft.Icons.ADD, width=200,
                        on_click=lambda e: page.go("/admin/course/new"),
                    ),
                ],
            ),
        )

    body_controls = [
        theme.page_title("Vue d'ensemble"),
        theme.body("Aperçu de votre activité d'enseignement.", muted=True),
        ft.Container(height=16),
        kpi_row,
        ft.Container(height=16),
    ]
    if no_course_hint:
        body_controls.append(no_course_hint)
    else:
        body_controls += [completion_card, ft.Container(height=16), chart_card]
    body_controls.append(ft.Container(height=20))

    body = ft.Container(
        padding=ft.padding.symmetric(horizontal=24, vertical=20),
        content=ft.Column(scroll=ft.ScrollMode.AUTO, controls=body_controls),
    )

    return shell_view(page, title="Vue d'ensemble", body=body)
