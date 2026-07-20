import flet as ft

from services.supabase_service import db
from components import theme


def build_lesson_view(page: ft.Page, course_id: str, index: int) -> ft.View:
    """
    Affiche UNE leçon d'un cours (leçon n° `index`, 0-based dans l'ordre).
    Contenu riche : texte, vidéo (lien), support PDF téléchargeable.
    Navigation séquentielle : leçon précédente / suivante, ou évaluation finale.
    """
    course = db.get_course(course_id)
    lessons = db.get_lessons(course_id)

    # Garde-fou sur l'index.
    if not lessons:
        return ft.View(
            route=f"/course/{course_id}/lesson/{index}",
            bgcolor=theme.Colors.BG,
            appbar=theme.branded_appbar(
                "Leçon",
                leading=ft.IconButton(ft.Icons.ARROW_BACK, icon_color=theme.Colors.PRIMARY,
                                      on_click=lambda e: page.go(f"/course/{course_id}")),
            ),
            controls=[ft.Container(padding=20, content=theme.body("Aucune leçon disponible.", muted=True))],
        )

    index = max(0, min(index, len(lessons) - 1))
    lesson = lessons[index]
    total = len(lessons)

    # Leçons déjà terminées (pour l'état du bouton).
    completed_ids = set()
    try:
        res = (
            db.client.table("lesson_progress")
            .select("lesson_id")
            .eq("user_id", db.current_user.id)
            .execute()
        )
        completed_ids = {r["lesson_id"] for r in (res.data or [])}
    except Exception:
        pass

    is_done = lesson["id"] in completed_ids

    # --- Contrôles dynamiques (statut de complétion) ---
    status_icon = ft.Icon(
        ft.Icons.CHECK_CIRCLE if is_done else ft.Icons.RADIO_BUTTON_UNCHECKED,
        color=theme.Colors.SUCCESS if is_done else theme.Colors.TEXT_MUTED,
    )
    done_btn = ft.ElevatedButton(
        "Leçon terminée ✓" if is_done else "Marquer comme terminé",
        icon=ft.Icons.CHECK,
        disabled=is_done,
        style=ft.ButtonStyle(
            bgcolor=theme.Colors.SUCCESS if not is_done else theme.Colors.BORDER,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=theme.RADIUS_INPUT),
        ),
    )

    def mark_done(e):
        # Retour visuel immédiat pendant l'enregistrement (requête réseau).
        done_btn.text = "Enregistrement…"
        done_btn.disabled = True
        page.update()

        db.mark_lesson_complete(lesson["id"])
        done_btn.text = "Leçon terminée ✓"
        done_btn.style.bgcolor = theme.Colors.BORDER
        status_icon.name = ft.Icons.CHECK_CIRCLE
        status_icon.color = theme.Colors.SUCCESS
        page.update()

    done_btn.on_click = mark_done

    # --- Bloc contenu de la leçon ---
    content_children = [
        ft.Row([status_icon, theme.section_title(lesson["title"])], spacing=8),
        theme.body(f"Leçon {index + 1} sur {total}", muted=True),
        ft.Divider(height=20, color=theme.Colors.BORDER),
    ]

    text_content = lesson.get("content") or ""
    if text_content:
        content_children.append(ft.Text(text_content, size=14, color=theme.Colors.TEXT))

    # Vidéo : bouton d'ouverture (robuste web + desktop).
    if lesson.get("video_url"):
        content_children.append(ft.Container(height=8))
        content_children.append(
            ft.OutlinedButton(
                "Regarder la vidéo",
                icon=ft.Icons.PLAY_CIRCLE_OUTLINE,
                on_click=lambda e, url=lesson["video_url"]: page.launch_url(url),
                style=ft.ButtonStyle(color=theme.Colors.PRIMARY_ACTION),
            )
        )

    # Support PDF téléchargeable.
    if lesson.get("file_url"):
        content_children.append(ft.Container(height=8))
        content_children.append(
            ft.OutlinedButton(
                "Télécharger le support (PDF)",
                icon=ft.Icons.PICTURE_AS_PDF_OUTLINED,
                on_click=lambda e, url=lesson["file_url"]: page.launch_url(url),
                style=ft.ButtonStyle(color=theme.Colors.ERROR),
            )
        )

    lesson_card = theme.card(padding=20, content=ft.Column(spacing=8, controls=content_children))

    # --- Navigation séquentielle ---
    prev_btn = ft.TextButton(
        "← Précédente",
        disabled=(index == 0),
        on_click=lambda e: page.go(f"/course/{course_id}/lesson/{index - 1}"),
        style=ft.ButtonStyle(color=theme.Colors.PRIMARY_ACTION),
    )
    if index < total - 1:
        next_btn = theme.primary_button(
            "Leçon suivante →",
            width=180,
            on_click=lambda e: page.go(f"/course/{course_id}/lesson/{index + 1}"),
        )
    else:
        # Dernière leçon : on propose l'évaluation finale.
        next_btn = ft.ElevatedButton(
            "Passer l'évaluation 🎓",
            icon=ft.Icons.QUIZ_OUTLINED,
            width=200,
            height=48,
            on_click=lambda e: page.go(f"/course/{course_id}/quiz"),
            style=ft.ButtonStyle(
                bgcolor=theme.Colors.CERT,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=theme.RADIUS_INPUT),
            ),
        )

    nav_row = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[prev_btn, next_btn],
    )

    return ft.View(
        route=f"/course/{course_id}/lesson/{index}",
        bgcolor=theme.Colors.BG,
        appbar=theme.branded_appbar(
            course["title"] if course else "Leçon",
            leading=ft.IconButton(
                ft.Icons.ARROW_BACK,
                icon_color=theme.Colors.PRIMARY,
                tooltip="Retour au cours",
                on_click=lambda e: page.go(f"/course/{course_id}"),
            ),
        ),
        controls=[
            ft.Container(
                padding=20,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        lesson_card,
                        ft.Container(height=16),
                        ft.Row([done_btn], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Container(height=16),
                        nav_row,
                    ],
                ),
            )
        ],
    )
