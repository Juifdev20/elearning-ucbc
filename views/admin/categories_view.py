import flet as ft

from components import theme
from components.app_shell import shell_view


def build_categories_view(page: ft.Page) -> ft.View:
    """Vue ADMIN : catégories de cours utilisées, avec renommage groupé."""
    try:
        categories = page.db.get_categories_summary()
    except Exception:
        categories = []

    def rename_dialog(category, count):
        new_field = ft.TextField(
            label="Nouveau nom de catégorie", value=category,
            border_radius=theme.RADIUS_INPUT, border_color=theme.Colors.BORDER,
            focused_border_color=theme.Colors.PRIMARY_ACTION,
        )
        feedback = ft.Text("", size=12, color=theme.Colors.ERROR)

        def save(e):
            new_name = (new_field.value or "").strip()
            if not new_name:
                feedback.value = "Le nom ne peut pas être vide."
                page.update()
                return
            try:
                page.db.rename_category(category, new_name)
                page.close(dlg)
                page.go("/admin/categories")  # reconstruit la liste
            except Exception:
                feedback.value = "Écriture refusée (policies RLS / rôle formateur ?)."
                page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Renommer « {category} »"),
            content=ft.Container(
                width=300,
                content=ft.Column(
                    tight=True,
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        ft.Text(f"{count} cours utilisent cette catégorie. "
                                "Ils seront tous mis à jour.", size=13,
                                color=theme.Colors.TEXT_MUTED),
                        new_field,
                        feedback,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Annuler", on_click=lambda e: page.close(dlg)),
                ft.TextButton("Renommer", on_click=save,
                              style=ft.ButtonStyle(color=theme.Colors.PRIMARY_ACTION)),
            ],
        )
        return lambda e: page.open(dlg)

    palette = [theme.Colors.PRIMARY_ACTION, theme.Colors.PURPLE, theme.Colors.TEAL,
              theme.Colors.CERT, theme.Colors.SUCCESS]

    def category_row(item, index):
        color = palette[index % len(palette)]
        return theme.card(
            padding=14,
            content=ft.Row(
                spacing=14,
                controls=[
                    theme.tinted_icon(ft.Icons.SELL_OUTLINED, color, box=44, size=20),
                    ft.Column(
                        expand=True,
                        spacing=2,
                        controls=[
                            ft.Text(item["category"], weight=ft.FontWeight.W_700, size=14,
                                    color=theme.Colors.TEXT),
                            ft.Text(f"{item['count']} cours", size=12,
                                    color=theme.Colors.TEXT_MUTED),
                        ],
                    ),
                    ft.TextButton(
                        "Renommer", icon=ft.Icons.EDIT_OUTLINED,
                        on_click=rename_dialog(item["category"], item["count"]),
                        style=ft.ButtonStyle(color=theme.Colors.PRIMARY_ACTION),
                    ),
                ],
            ),
        )

    rows = [category_row(item, i) for i, item in enumerate(categories)] if categories else [
        theme.body("Aucune catégorie pour l'instant : créez un cours pour en voir apparaître.",
                   muted=True)
    ]

    body = ft.Container(
        padding=ft.padding.symmetric(horizontal=24, vertical=20),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                theme.page_title("Catégories de cours"),
                theme.body("Renommez une catégorie pour la mettre à jour sur tous les cours concernés.",
                           muted=True),
                ft.Container(height=16),
                ft.Column(spacing=10, controls=rows),
                ft.Container(height=20),
            ],
        ),
    )

    return shell_view(page, title="Catégories", body=body)
