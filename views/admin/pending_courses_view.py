import flet as ft

from services.supabase_service import db
from components import theme
from components.app_shell import shell_view


def build_pending_courses_view(page: ft.Page) -> ft.View:
    """Vue ADMIN : file d'attente des cours soumis par les formateurs, à valider."""
    try:
        pending = db.get_pending_courses()
        unavailable = False
    except Exception:
        pending = []
        unavailable = True

    def approve(course_id):
        def handler(e):
            try:
                db.approve_course(course_id)
            except Exception:
                pass
            page.go("/admin/pending-courses")
        return handler

    def reject_dialog(course_id, title):
        reason_f = ft.TextField(
            label="Motif du rejet (visible par le formateur)",
            multiline=True, min_lines=2, max_lines=4,
            border_radius=theme.RADIUS_INPUT, border_color=theme.Colors.BORDER,
            focused_border_color=theme.Colors.PRIMARY_ACTION,
        )

        def confirm(e):
            try:
                db.reject_course(course_id, reason_f.value.strip())
            except Exception:
                pass
            page.close(dlg)
            page.go("/admin/pending-courses")

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Rejeter « {title} » ?"),
            content=ft.Container(width=380, content=reason_f),
            actions=[
                ft.TextButton("Annuler", on_click=lambda e: page.close(dlg)),
                ft.TextButton("Rejeter", on_click=confirm,
                              style=ft.ButtonStyle(color=theme.Colors.ERROR)),
            ],
        )
        return lambda e: page.open(dlg)

    def pending_row(course):
        cid = course["id"]
        author = (course.get("profiles") or {}).get("full_name", "Formateur")
        return theme.card(
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Row(
                        spacing=14,
                        controls=[
                            theme.tinted_icon(ft.Icons.PENDING_ACTIONS, theme.Colors.CERT,
                                              box=48, size=22),
                            ft.Column(
                                expand=True,
                                spacing=3,
                                controls=[
                                    theme.subtitle(course.get("title", "Cours")),
                                    ft.Text(f"Par {author} · {course.get('category', '') or 'Sans catégorie'}",
                                            size=12, color=theme.Colors.TEXT_MUTED),
                                ],
                            ),
                        ],
                    ),
                    ft.Text(course.get("description", "") or "", size=13,
                            color=theme.Colors.TEXT, max_lines=3,
                            overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.TextButton(
                                "Aperçu", icon=ft.Icons.VISIBILITY_OUTLINED,
                                on_click=lambda e, c=cid: page.go(f"/admin/course/{c}"),
                                style=ft.ButtonStyle(color=theme.Colors.PRIMARY_ACTION),
                            ),
                            theme.primary_button(
                                "Approuver", icon=ft.Icons.CHECK, width=160,
                                on_click=approve(cid),
                            ),
                            ft.OutlinedButton(
                                "Rejeter", icon=ft.Icons.CLOSE,
                                on_click=reject_dialog(cid, course.get("title", "Cours")),
                                style=ft.ButtonStyle(color=theme.Colors.ERROR),
                            ),
                        ],
                    ),
                ],
            ),
        )

    if unavailable:
        rows = [
            theme.card(
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                    controls=[
                        theme.tinted_icon(ft.Icons.WARNING_AMBER_ROUNDED, theme.Colors.CERT,
                                          box=56, size=26),
                        theme.body("Fonctionnalité indisponible : exécutez sql/course_approval.sql "
                                   "dans Supabase pour l'activer.", muted=True),
                    ],
                ),
            )
        ]
    elif pending:
        rows = [pending_row(c) for c in pending]
    else:
        rows = [
            theme.card(
                padding=32,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                    controls=[
                        theme.tinted_icon(ft.Icons.CHECK_CIRCLE_OUTLINE, theme.Colors.SUCCESS,
                                          box=64, size=32, radius=18),
                        theme.subtitle("Aucun cours en attente"),
                        theme.body("Tous les cours soumis par les formateurs ont été traités.",
                                   muted=True),
                    ],
                ),
            )
        ]

    body = ft.Container(
        padding=ft.padding.symmetric(horizontal=24, vertical=20),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                theme.page_title("Cours à valider"),
                theme.body(f"{len(pending)} cours en attente de validation.", muted=True),
                ft.Container(height=16),
                ft.Column(spacing=12, controls=rows),
                ft.Container(height=20),
            ],
        ),
    )

    return shell_view(page, title="Cours à valider", body=body)
