import flet as ft

from services.supabase_service import db
from components import theme
from components.app_shell import shell_view


def build_progress_view(page: ft.Page) -> ft.View:
    """Onglet PROGRESSION : vue d'ensemble de l'avancement sur tous les cours."""
    try:
        enrollments = db.get_my_enrollments()
    except Exception:
        enrollments = []
    try:
        certificates = db.get_my_certificates()
    except Exception:
        certificates = []
    try:
        activity = db.get_my_activity_feed(limit=15)
    except Exception:
        activity = []

    # Calcul des statistiques globales.
    per_course = []  # (titre, progression%)
    completed_count = 0
    total_progress = 0
    for en in enrollments:
        course = en.get("courses") or {}
        try:
            p = db.get_course_progress(course.get("id", ""))
        except Exception:
            p = 0
        per_course.append((course.get("title", "Cours"), p))
        total_progress += p
        if p >= 100:
            completed_count += 1

    avg_progress = round(total_progress / len(per_course), 0) if per_course else 0

    stats = ft.ResponsiveRow(
        spacing=14,
        run_spacing=14,
        controls=[
            theme.stat_card(ft.Icons.MENU_BOOK, "Cours suivis", len(enrollments),
                            theme.Colors.PRIMARY_ACTION, col={"xs": 12, "sm": 6, "md": 3}),
            theme.stat_card(ft.Icons.CHECK_CIRCLE, "Cours terminés", completed_count,
                            theme.Colors.SUCCESS, col={"xs": 12, "sm": 6, "md": 3}),
            theme.stat_card(ft.Icons.WORKSPACE_PREMIUM, "Brevets obtenus", len(certificates),
                            theme.Colors.CERT, col={"xs": 12, "sm": 6, "md": 3}),
            theme.stat_card(ft.Icons.TRENDING_UP, "Progression moyenne", f"{int(avg_progress)}%",
                            theme.Colors.PURPLE, col={"xs": 12, "sm": 6, "md": 3}),
        ],
    )

    # Détail par cours.
    if per_course:
        detail_rows = [
            theme.card(
                content=ft.Row(
                    spacing=14,
                    controls=[
                        theme.tinted_icon(
                            ft.Icons.CHECK_CIRCLE if p >= 100 else ft.Icons.PLAY_LESSON,
                            theme.Colors.SUCCESS if p >= 100 else theme.Colors.PRIMARY_ACTION,
                        ),
                        ft.Column(
                            expand=True,
                            spacing=6,
                            controls=[
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls=[
                                        theme.subtitle(title),
                                        ft.Text(f"{int(p)}%", size=14, weight=ft.FontWeight.BOLD,
                                                color=theme.Colors.SUCCESS if p >= 100
                                                else theme.Colors.PRIMARY_ACTION),
                                    ],
                                ),
                                theme.progress_bar(p),
                            ],
                        ),
                    ],
                ),
            )
            for (title, p) in per_course
        ]
        detail = ft.Column(spacing=12, controls=detail_rows)
    else:
        detail = theme.card(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    theme.tinted_icon(ft.Icons.TRENDING_UP, theme.Colors.PRIMARY_ACTION, box=56, size=28),
                    theme.body("Commencez un cours pour suivre votre progression ici.", muted=True),
                ],
            ),
        )

    # Historique d'activité (chronologique, tous types d'événements confondus).
    _EVENT_ICONS = {
        "enrollment": (ft.Icons.HOW_TO_REG, theme.Colors.PURPLE),
        "lesson": (ft.Icons.CHECK_CIRCLE, theme.Colors.SUCCESS),
        "quiz": (ft.Icons.QUIZ, theme.Colors.PRIMARY_ACTION),
        "certificate": (ft.Icons.WORKSPACE_PREMIUM, theme.Colors.CERT),
    }

    def event_label(ev: dict) -> str:
        etype = ev.get("type")
        course = ev.get("course_title", "Cours")
        if etype == "enrollment":
            return f"Inscription au cours « {course} »"
        if etype == "lesson":
            return f"Leçon « {ev.get('lesson_title', '')} » terminée — {course}"
        if etype == "quiz":
            status = "réussi ✅" if ev.get("passed") else "échoué ❌"
            return f"Quiz {status} ({ev.get('score', 0)}%) — {course}"
        if etype == "certificate":
            return f"Certificat obtenu — {course}"
        return course

    def activity_row(ev: dict):
        icon, color = _EVENT_ICONS.get(ev.get("type"), (ft.Icons.CIRCLE, theme.Colors.TEXT_MUTED))
        date = (ev.get("date") or "")[:16].replace("T", " à ")
        return ft.Row(
            spacing=12,
            controls=[
                theme.tinted_icon(icon, color, box=36, size=17),
                ft.Column(
                    expand=True,
                    spacing=1,
                    controls=[
                        ft.Text(event_label(ev), size=13, color=theme.Colors.TEXT),
                        ft.Text(date, size=11, color=theme.Colors.TEXT_MUTED),
                    ],
                ),
            ],
        )

    if activity:
        activity_content = ft.Column(spacing=14, controls=[activity_row(ev) for ev in activity])
    else:
        activity_content = theme.body("Aucune activité pour l'instant.", muted=True)

    body = ft.Container(
        padding=ft.padding.symmetric(horizontal=24, vertical=20),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                theme.page_title("Ma progression"),
                theme.body("Suivez votre avancement sur chaque cours.", muted=True),
                ft.Container(height=16),
                stats,
                ft.Container(height=20),
                theme.section_title("Détail par cours"),
                ft.Container(height=8),
                detail,
                ft.Container(height=20),
                theme.section_title("Historique d'activité"),
                ft.Container(height=8),
                theme.card(content=activity_content),
                ft.Container(height=20),
            ],
        ),
    )

    return shell_view(page, title="Progression", body=body)
