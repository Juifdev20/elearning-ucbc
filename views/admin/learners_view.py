import flet as ft

from services.supabase_service import db
from components import theme


def build_learners_view(page: ft.Page, course_id: str) -> ft.View:
    """Vue formateur : apprenants inscrits à un cours et leur progression."""
    course = db.get_course(course_id)
    try:
        learners = db.get_course_learners(course_id)
    except Exception:
        learners = []

    # Trie par progression décroissante (les plus avancés en tête).
    learners.sort(key=lambda x: x.get("progress", 0), reverse=True)

    def learner_row(learner):
        name = learner.get("full_name", "Apprenant")
        p = learner.get("progress", 0)
        return theme.card(
            padding=14,
            content=ft.Row(
                spacing=12,
                controls=[
                    ft.CircleAvatar(
                        content=ft.Text(name[:1].upper(), weight=ft.FontWeight.BOLD),
                        radius=18, bgcolor=theme.Colors.PRIMARY, color=ft.Colors.WHITE,
                    ),
                    ft.Column(
                        expand=True,
                        spacing=4,
                        controls=[
                            ft.Text(name, weight=ft.FontWeight.W_600, color=theme.Colors.TEXT),
                            theme.progress_bar(p),
                        ],
                    ),
                    ft.Text(f"{int(p)}%", weight=ft.FontWeight.BOLD,
                            color=theme.Colors.SUCCESS if p >= 100 else theme.Colors.PRIMARY_ACTION),
                ],
            ),
        )

    if learners:
        completed = sum(1 for l in learners if l.get("progress", 0) >= 100)
        summary = theme.body(
            f"{len(learners)} inscrit(s) · {completed} ont terminé le cours", muted=True)
        rows = [learner_row(l) for l in learners]
    else:
        summary = theme.body("Aucun apprenant inscrit à ce cours pour l'instant.", muted=True)
        rows = []

    return ft.View(
        route=f"/admin/course/{course_id}/learners",
        bgcolor=theme.Colors.BG,
        appbar=theme.branded_appbar(
            f"Apprenants — {course['title'] if course else 'Cours'}",
            leading=ft.IconButton(ft.Icons.ARROW_BACK, icon_color=theme.Colors.PRIMARY,
                                  on_click=lambda e: page.go(f"/admin/course/{course_id}")),
        ),
        controls=[
            ft.Container(
                padding=20,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        theme.page_title("Suivi des apprenants"),
                        summary,
                        ft.Container(height=10),
                        ft.Column(spacing=10, controls=rows),
                    ],
                ),
            )
        ],
    )
