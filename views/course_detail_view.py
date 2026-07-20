import flet as ft

from services.supabase_service import db
from components import theme


def build_course_detail_view(page: ft.Page, course_id: str) -> ft.View:
    course = db.get_course(course_id)
    lessons = db.get_lessons(course_id)
    db.enroll(course_id)  # inscrit automatiquement l'utilisateur au premier accès

    completed_lesson_ids = set()
    try:
        res = (
            db.client.table("lesson_progress")
            .select("lesson_id")
            .eq("user_id", db.current_user.id)
            .execute()
        )
        completed_lesson_ids = {r["lesson_id"] for r in (res.data or [])}
    except Exception:
        pass

    progress = db.get_course_progress(course_id)

    def open_lesson(index):
        return lambda e: page.go(f"/course/{course_id}/lesson/{index}")

    def _lesson_tile(lesson, index, is_done):
        return theme.card(
            padding=14,
            on_click=open_lesson(index),
            ink=True,
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE if is_done else ft.Icons.PLAY_CIRCLE_OUTLINE,
                        color=theme.Colors.SUCCESS if is_done else theme.Colors.PRIMARY_ACTION,
                    ),
                    ft.Column(
                        expand=True,
                        spacing=2,
                        controls=[
                            ft.Text(f"{index + 1}. {lesson['title']}", weight=ft.FontWeight.W_600, color=theme.Colors.TEXT),
                            ft.Text(
                                (lesson.get("content") or "")[:80] + ("..." if len(lesson.get("content") or "") > 80 else ""),
                                size=12,
                                color=theme.Colors.TEXT_MUTED,
                            ),
                        ],
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color=theme.Colors.TEXT_MUTED),
                ]
            ),
        )

    lesson_tiles = [
        _lesson_tile(lesson, i, lesson["id"] in completed_lesson_ids)
        for i, lesson in enumerate(lessons)
    ]

    # Bouton "Commencer / Continuer" : ouvre la première leçon non terminée.
    first_unfinished = next(
        (i for i, l in enumerate(lessons) if l["id"] not in completed_lesson_ids), 0
    )
    start_label = "Commencer le cours" if progress == 0 else "Continuer le cours"
    start_btn = theme.primary_button(
        start_label,
        icon=ft.Icons.PLAY_ARROW,
        on_click=open_lesson(first_unfinished),
    ) if lessons else ft.Container()

    # L'évaluation ne se débloque qu'une fois toutes les leçons terminées
    # (sinon un certificat pourrait être obtenu sans avoir suivi le cours).
    can_take_quiz = (not lessons) or progress >= 100

    if can_take_quiz:
        quiz_btn = theme.primary_button(
            "Passer l'évaluation finale 🎓",
            icon=ft.Icons.QUIZ_OUTLINED,
            on_click=lambda e: page.go(f"/course/{course_id}/quiz"),
        )
    else:
        quiz_btn = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
            controls=[
                ft.ElevatedButton(
                    "Passer l'évaluation finale 🎓",
                    icon=ft.Icons.LOCK_OUTLINE,
                    disabled=True,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=theme.RADIUS_INPUT)),
                ),
                theme.body("Terminez toutes les leçons pour débloquer l'évaluation.", muted=True),
            ],
        )

    return ft.View(
        route=f"/course/{course_id}",
        bgcolor=theme.Colors.BG,
        appbar=theme.branded_appbar(
            course["title"] if course else "Cours",
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                icon_color=theme.Colors.PRIMARY,
                on_click=lambda e: page.go("/dashboard"),
            ),
        ),
        controls=[
            ft.Container(
                padding=20,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        theme.body(course.get("description", "") if course else "", muted=True),
                        ft.Container(height=6),
                        theme.progress_bar(progress),
                        ft.Text(f"{progress}% de progression", size=12, color=theme.Colors.TEXT_MUTED),
                        ft.Container(height=10),
                        ft.Row([start_btn], alignment=ft.MainAxisAlignment.CENTER) if lessons else ft.Container(),
                        ft.Container(height=14),
                        theme.section_title("Contenu du cours"),
                        ft.Column(spacing=10, controls=lesson_tiles) if lesson_tiles
                        else theme.body("Aucune leçon pour ce cours.", muted=True),
                        ft.Container(height=20),
                        ft.Row([quiz_btn], alignment=ft.MainAxisAlignment.CENTER),
                    ]
                ),
            )
        ],
    )
