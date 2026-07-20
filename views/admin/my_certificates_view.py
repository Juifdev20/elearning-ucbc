import flet as ft

from services.supabase_service import db
from components import theme
from components.app_shell import shell_view


def build_my_certificates_view(page: ft.Page) -> ft.View:
    """Vue FORMATEUR : certificats délivrés pour ses propres cours."""
    try:
        certificates = db.get_my_issued_certificates()
    except Exception:
        certificates = []

    all_rows = [
        (
            (cert.get("profiles") or {}).get("full_name", "Apprenant"),
            (cert.get("courses") or {}).get("title", "Cours"),
            (cert.get("issued_at") or "")[:10],
        )
        for cert in certificates
    ]

    def cert_row(student, course_title, issued_at):
        return theme.card(
            padding=14,
            content=ft.Row(
                spacing=14,
                controls=[
                    theme.tinted_icon(ft.Icons.WORKSPACE_PREMIUM, theme.Colors.CERT, box=44, size=22),
                    ft.Column(
                        expand=True,
                        spacing=2,
                        controls=[
                            ft.Text(student, weight=ft.FontWeight.W_700, size=14,
                                    color=theme.Colors.TEXT),
                            ft.Text(course_title, size=12, color=theme.Colors.TEXT_MUTED),
                        ],
                    ),
                    ft.Text(issued_at, size=12, color=theme.Colors.TEXT_MUTED),
                ],
            ),
        )

    rows_col = ft.Column(spacing=10)
    empty_msg = theme.body("Aucun certificat ne correspond à votre recherche.", muted=True)
    empty_msg.visible = False

    def apply_search(e=None):
        q = (search_field.value or "").strip().lower()
        filtered = [r for r in all_rows if q in r[0].lower() or q in r[1].lower()] if q else all_rows
        rows_col.controls = [cert_row(*r) for r in filtered]
        empty_msg.visible = len(filtered) == 0 and len(all_rows) > 0
        page.update()

    search_field = ft.TextField(
        hint_text="Rechercher par apprenant ou cours…",
        prefix_icon=ft.Icons.SEARCH,
        border_radius=30,
        border_color=theme.Colors.BORDER,
        focused_border_color=theme.Colors.PRIMARY_ACTION,
        bgcolor=theme.Colors.SURFACE,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=8),
        on_change=apply_search,
    )

    rows_col.controls = [cert_row(*r) for r in all_rows] if all_rows else [
        theme.card(
            padding=32,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    theme.tinted_icon(ft.Icons.WORKSPACE_PREMIUM, theme.Colors.CERT,
                                      box=64, size=32, radius=18),
                    theme.subtitle("Aucun certificat délivré pour l'instant"),
                    theme.body("Les certificats apparaîtront ici dès qu'un apprenant réussira "
                               "le quiz de l'un de vos cours.", muted=True),
                ],
            ),
        )
    ]

    body = ft.Container(
        padding=ft.padding.symmetric(horizontal=24, vertical=20),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                theme.page_title("Certificats délivrés"),
                theme.body(f"{len(all_rows)} certificat(s) pour vos cours.", muted=True),
                ft.Container(height=16),
                search_field,
                ft.Container(height=12),
                empty_msg,
                rows_col,
                ft.Container(height=20),
            ],
        ),
    )

    return shell_view(page, title="Mes certificats", body=body)
