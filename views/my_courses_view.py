import flet as ft

from services.supabase_service import db
from components import theme
from components.app_shell import shell_view


def build_my_courses_view(page: ft.Page) -> ft.View:
    """Onglet MES COURS : liste des cours auxquels l'utilisateur est inscrit."""
    try:
        enrollments = db.get_my_enrollments()
    except Exception:
        enrollments = []

    def open_course(course_id):
        return lambda e: page.go(f"/course/{course_id}")

    def enrollment_row(enrollment):
        course = enrollment.get("courses") or {}
        course_id = course.get("id", "")
        try:
            progress = db.get_course_progress(course_id)
        except Exception:
            progress = 0
        done = progress >= 100

        return theme.card(
            on_click=open_course(course_id),
            ink=True,
            content=ft.Row(
                spacing=14,
                controls=[
                    theme.tinted_icon(
                        ft.Icons.CHECK_CIRCLE if done else ft.Icons.MENU_BOOK_ROUNDED,
                        theme.Colors.SUCCESS if done else theme.Colors.PRIMARY_ACTION,
                        box=52, size=24,
                    ),
                    ft.Column(
                        expand=True,
                        spacing=6,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    theme.subtitle(course.get("title", "Cours")),
                                    theme.chip("Terminé ✓", theme.Colors.SUCCESS) if done
                                    else theme.chip("En cours", theme.Colors.PRIMARY_ACTION),
                                ],
                            ),
                            theme.progress_bar(progress),
                            ft.Text(f"{int(progress)}% terminé", size=11,
                                    color=theme.Colors.TEXT_MUTED),
                        ],
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color=theme.Colors.TEXT_MUTED),
                ],
            ),
        )

    if enrollments:
        content = ft.Column(spacing=12, controls=[enrollment_row(en) for en in enrollments])
    else:
        content = theme.card(
            padding=32,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                controls=[
                    theme.tinted_icon(ft.Icons.SCHOOL_OUTLINED, theme.Colors.PRIMARY_ACTION,
                                      box=64, size=32, radius=18),
                    theme.subtitle("Aucun cours pour l'instant"),
                    theme.body("Inscrivez-vous à un cours depuis le catalogue.", muted=True),
                    ft.Container(height=4),
                    theme.primary_button(
                        "Découvrir le catalogue",
                        icon=ft.Icons.EXPLORE_OUTLINED,
                        width=240,
                        on_click=lambda e: page.go("/dashboard"),
                    ),
                ],
            ),
        )

    body = ft.Container(
        padding=ft.padding.symmetric(horizontal=24, vertical=20),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                theme.page_title("Mes cours"),
                theme.body("Reprenez là où vous vous êtes arrêté.", muted=True),
                ft.Container(height=14),
                content,
                ft.Container(height=20),
            ],
        ),
    )

    return shell_view(page, title="Mes cours", body=body)
