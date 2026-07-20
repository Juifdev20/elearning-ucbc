import flet as ft

from components import theme
from components.app_shell import shell_view


def build_announcements_view(page: ft.Page) -> ft.View:
    """Vue ADMIN : diffusion d'annonces vers tous les utilisateurs (cloche 🔔)."""
    try:
        announcements = page.db.get_announcements(limit=30)
    except Exception:
        announcements = None  # None = table absente (migration non exécutée)

    title_field = ft.TextField(
        label="Titre de l'annonce", border_radius=theme.RADIUS_INPUT,
        border_color=theme.Colors.BORDER, focused_border_color=theme.Colors.PRIMARY_ACTION,
    )
    message_field = ft.TextField(
        label="Message", multiline=True, min_lines=3, max_lines=6,
        border_radius=theme.RADIUS_INPUT, border_color=theme.Colors.BORDER,
        focused_border_color=theme.Colors.PRIMARY_ACTION,
    )
    feedback = ft.Text("", size=12)

    def publish(e):
        feedback.value = ""
        if not title_field.value or not title_field.value.strip():
            feedback.value = "Le titre est obligatoire."
            feedback.color = theme.Colors.ERROR
            page.update()
            return
        try:
            page.db.create_announcement(title_field.value.strip(),
                                   (message_field.value or "").strip())
            page.go("/admin/announcements")  # reconstruit la liste
        except Exception:
            feedback.value = "Écriture refusée. Avez-vous exécuté sql/announcements.sql ?"
            feedback.color = theme.Colors.ERROR
            page.update()

    def delete_announcement(ann_id):
        def handler(e):
            try:
                page.db.delete_announcement(ann_id)
            except Exception:
                pass
            page.go("/admin/announcements")
        return handler

    publish_card = theme.card(
        content=ft.Column(
            spacing=10,
            controls=[
                theme.section_title("Publier une annonce"),
                theme.body("Visible par tous les utilisateurs connectés, via la cloche 🔔.",
                           muted=True),
                title_field,
                message_field,
                feedback,
                theme.primary_button("Publier", icon=ft.Icons.CAMPAIGN_OUTLINED,
                                     width=200, on_click=publish),
            ],
        ),
    )

    def ann_row(ann):
        author = (ann.get("profiles") or {}).get("full_name", "Équipe pédagogique")
        created = (ann.get("created_at") or "")[:16].replace("T", " à ")
        return theme.card(
            padding=14,
            content=ft.Row(
                spacing=14,
                controls=[
                    theme.tinted_icon(ft.Icons.CAMPAIGN, theme.Colors.PRIMARY_ACTION, box=44, size=20),
                    ft.Column(
                        expand=True,
                        spacing=3,
                        controls=[
                            ft.Text(ann.get("title", ""), weight=ft.FontWeight.W_700, size=14,
                                    color=theme.Colors.TEXT,
                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(ann.get("message", ""), size=12, color=theme.Colors.TEXT_MUTED,
                                    max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(f"Par {author} · {created}", size=11,
                                    color=theme.Colors.TEXT_MUTED),
                        ],
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE, icon_color=theme.Colors.ERROR,
                        tooltip="Supprimer", on_click=delete_announcement(ann["id"]),
                    ),
                ],
            ),
        )

    if announcements is None:
        history = theme.card(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    theme.tinted_icon(ft.Icons.WARNING_AMBER_ROUNDED, theme.Colors.CERT,
                                      box=56, size=26),
                    theme.body("Fonctionnalité indisponible : exécutez sql/announcements.sql "
                               "dans Supabase pour l'activer.", muted=True),
                ],
            ),
        )
    elif announcements:
        history = ft.Column(spacing=10, controls=[ann_row(a) for a in announcements])
    else:
        history = theme.body("Aucune annonce publiée pour l'instant.", muted=True)

    body = ft.Container(
        padding=ft.padding.symmetric(horizontal=24, vertical=20),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                theme.page_title("Annonces"),
                ft.Container(height=16),
                publish_card,
                ft.Container(height=20),
                theme.section_title("Historique"),
                ft.Container(height=8),
                history,
                ft.Container(height=20),
            ],
        ),
    )

    return shell_view(page, title="Annonces", body=body)
