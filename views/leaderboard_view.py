import flet as ft

from components import theme
from components.app_shell import shell_view

_MEDALS = {0: ("🥇", "#F59E0B"), 1: ("🥈", "#9CA3AF"), 2: ("🥉", "#B45309")}


def build_leaderboard_view(page: ft.Page) -> ft.View:
    """Onglet CLASSEMENT : gamification — top apprenants de la plateforme."""
    my_id = page.db.current_user.id if page.db.current_user else None
    try:
        ranking = page.db.get_leaderboard(limit_n=20)
        unavailable = False
    except Exception:
        ranking = []
        unavailable = True

    def rank_row(entry, index):
        is_me = entry.get("user_id") == my_id
        medal, medal_color = _MEDALS.get(index, (None, None))

        rank_widget = (
            ft.Text(medal, size=22)
            if medal else
            ft.Container(
                width=32, height=32, border_radius=16,
                bgcolor=theme.tint(theme.Colors.TEXT_MUTED, 0.15),
                alignment=ft.alignment.center,
                content=ft.Text(str(index + 1), size=13, weight=ft.FontWeight.BOLD,
                                color=theme.Colors.TEXT_MUTED),
            )
        )

        return theme.card(
            padding=14,
            bgcolor=theme.tint(theme.Colors.PRIMARY_ACTION, 0.08) if is_me else theme.Colors.SURFACE,
            content=ft.Row(
                spacing=14,
                controls=[
                    ft.Container(width=32, alignment=ft.alignment.center, content=rank_widget),
                    ft.CircleAvatar(
                        content=ft.Text((entry.get("full_name") or "?")[:1].upper(),
                                        weight=ft.FontWeight.BOLD),
                        radius=20,
                        bgcolor=theme.tint(medal_color or theme.Colors.PRIMARY_ACTION, 0.9),
                        color=ft.Colors.WHITE,
                    ),
                    ft.Column(
                        expand=True,
                        spacing=2,
                        controls=[
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Container(
                                        expand=True,
                                        content=ft.Text(entry.get("full_name", "Apprenant"),
                                                        weight=ft.FontWeight.W_700, size=14,
                                                        color=theme.Colors.TEXT,
                                                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                    ),
                                    theme.chip("Vous", theme.Colors.SUCCESS) if is_me else ft.Container(),
                                ],
                            ),
                            ft.Text(
                                f"{entry.get('courses_completed', 0)} cours terminé(s) · "
                                f"{entry.get('lessons_completed', 0)} leçon(s)",
                                size=11, color=theme.Colors.TEXT_MUTED,
                            ),
                        ],
                    ),
                    ft.Row(
                        spacing=4,
                        controls=[
                            ft.Icon(ft.Icons.WORKSPACE_PREMIUM, size=16, color=theme.Colors.CERT),
                            ft.Text(str(entry.get("certificates_count", 0)), size=15,
                                    weight=ft.FontWeight.BOLD, color=theme.Colors.CERT),
                        ],
                    ),
                ],
            ),
        )

    if unavailable:
        content = theme.card(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    theme.tinted_icon(ft.Icons.WARNING_AMBER_ROUNDED, theme.Colors.CERT, box=56, size=26),
                    theme.body("Classement indisponible : exécutez sql/leaderboard.sql "
                               "dans Supabase pour l'activer.", muted=True),
                ],
            ),
        )
    elif ranking:
        content = ft.Column(spacing=10, controls=[rank_row(e, i) for i, e in enumerate(ranking)])
    else:
        content = theme.body("Aucun apprenant classé pour l'instant.", muted=True)

    body = ft.Container(
        padding=ft.padding.symmetric(horizontal=24, vertical=20),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                theme.page_title("Classement 🏆"),
                theme.body("Les apprenants les plus assidus de la plateforme.", muted=True),
                ft.Container(height=16),
                content,
                ft.Container(height=20),
            ],
        ),
    )

    return shell_view(page, title="Classement", body=body)
