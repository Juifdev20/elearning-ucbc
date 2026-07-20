import flet as ft

from services.supabase_service import db
from components import theme
from components.app_shell import shell_view


def build_my_students_view(page: ft.Page) -> ft.View:
    """Vue FORMATEUR : tous les apprenants inscrits à l'un de ses cours."""
    try:
        rows = db.get_my_students()
    except Exception:
        rows = []

    distinct_students = {r["student_name"] for r in rows}
    completed = sum(1 for r in rows if r["progress"] >= 100)

    stats = ft.ResponsiveRow(
        spacing=14,
        run_spacing=14,
        controls=[
            theme.stat_card(ft.Icons.GROUP, "Apprenants uniques", len(distinct_students),
                            theme.Colors.PRIMARY_ACTION, col={"xs": 12, "sm": 4}),
            theme.stat_card(ft.Icons.HOW_TO_REG, "Inscriptions", len(rows),
                            theme.Colors.PURPLE, col={"xs": 12, "sm": 4}),
            theme.stat_card(ft.Icons.CHECK_CIRCLE, "Cours terminés", completed,
                            theme.Colors.SUCCESS, col={"xs": 12, "sm": 4}),
        ],
    )

    def student_row(r):
        p = r["progress"]
        return theme.card(
            padding=14,
            content=ft.Row(
                spacing=14,
                controls=[
                    ft.CircleAvatar(
                        content=ft.Text((r["student_name"] or "?")[:1].upper(),
                                        weight=ft.FontWeight.BOLD),
                        radius=20,
                        bgcolor=theme.tint(theme.Colors.PRIMARY_ACTION, 0.9),
                        color=ft.Colors.WHITE,
                    ),
                    ft.Column(
                        expand=True,
                        spacing=5,
                        controls=[
                            ft.Text(r["student_name"], weight=ft.FontWeight.W_700, size=14,
                                    color=theme.Colors.TEXT),
                            ft.Text(r["course_title"], size=12, color=theme.Colors.TEXT_MUTED),
                            theme.progress_bar(p),
                        ],
                    ),
                    ft.Text(f"{int(p)}%", size=14, weight=ft.FontWeight.BOLD,
                            color=theme.Colors.SUCCESS if p >= 100 else theme.Colors.PRIMARY_ACTION),
                ],
            ),
        )

    rows_col = ft.Column(spacing=10)
    empty_msg = theme.body("Aucun apprenant ne correspond à votre recherche.", muted=True)
    empty_msg.visible = False

    def apply_search(e=None):
        q = (search_field.value or "").strip().lower()
        filtered = [r for r in rows if q in r["student_name"].lower()
                   or q in r["course_title"].lower()] if q else rows
        rows_col.controls = [student_row(r) for r in filtered]
        empty_msg.visible = len(filtered) == 0 and len(rows) > 0
        page.update()

    search_field = ft.TextField(
        hint_text="Rechercher un apprenant ou un cours…",
        prefix_icon=ft.Icons.SEARCH,
        border_radius=30,
        border_color=theme.Colors.BORDER,
        focused_border_color=theme.Colors.PRIMARY_ACTION,
        bgcolor=theme.Colors.SURFACE,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=8),
        on_change=apply_search,
    )

    rows_col.controls = [student_row(r) for r in rows] if rows else [
        theme.card(
            padding=32,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    theme.tinted_icon(ft.Icons.GROUP_OUTLINED, theme.Colors.PRIMARY_ACTION,
                                      box=64, size=32, radius=18),
                    theme.subtitle("Aucun apprenant pour l'instant"),
                    theme.body("Vos apprenants apparaîtront ici dès qu'ils s'inscriront "
                               "à l'un de vos cours.", muted=True),
                ],
            ),
        )
    ]

    body = ft.Container(
        padding=ft.padding.symmetric(horizontal=24, vertical=20),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                theme.page_title("Mes apprenants"),
                theme.body("Tous les apprenants inscrits à vos cours.", muted=True),
                ft.Container(height=16),
                stats,
                ft.Container(height=20),
                search_field,
                ft.Container(height=12),
                empty_msg,
                rows_col,
                ft.Container(height=20),
            ],
        ),
    )

    return shell_view(page, title="Mes apprenants", body=body)
