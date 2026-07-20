"""
Écrans transitoires : chargement de page et erreur de chargement.

Le routeur (main.py) affiche `build_loading_view` IMMÉDIATEMENT à chaque
navigation, avant de construire la vraie vue (qui fait des requêtes réseau).
L'utilisateur a ainsi un retour visuel instantané dès son clic.
"""
import flet as ft

from components import theme
from components.app_shell import home_route


def build_loading_view(page: ft.Page) -> ft.View:
    """Écran de chargement : logo + anneau de progression + message."""
    return ft.View(
        route=page.route,
        bgcolor=theme.Colors.BG,
        padding=0,
        controls=[
            ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                    controls=[
                        theme.brand_logo(size=64),
                        ft.ProgressRing(
                            width=28, height=28, stroke_width=3,
                            color=theme.Colors.PRIMARY_ACTION,
                        ),
                        ft.Text("Chargement…", size=13, weight=ft.FontWeight.W_500,
                                color=theme.Colors.TEXT_MUTED),
                    ],
                ),
            )
        ],
    )


def loading_body() -> ft.Container:
    """Petit spinner centré à afficher DANS la zone de contenu du shell.

    Utilisé pour la navigation via la sidebar / barre du bas : la coquille
    (menu, topbar) reste visible, seul le contenu indique le chargement.
    """
    return ft.Container(
        expand=True,
        alignment=ft.alignment.center,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=12,
            controls=[
                ft.ProgressRing(width=26, height=26, stroke_width=3,
                                color=theme.Colors.PRIMARY_ACTION),
                ft.Text("Chargement…", size=12, color=theme.Colors.TEXT_MUTED),
            ],
        ),
    )


def build_error_view(page: ft.Page, on_retry) -> ft.View:
    """Écran d'erreur de chargement, avec bouton Réessayer."""
    return ft.View(
        route=page.route,
        bgcolor=theme.Colors.BG,
        padding=0,
        controls=[
            ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=14,
                    controls=[
                        theme.tinted_icon(ft.Icons.WIFI_OFF_ROUNDED, theme.Colors.ERROR,
                                          box=72, size=36, radius=20),
                        ft.Text("Impossible de charger la page", size=18,
                                weight=ft.FontWeight.BOLD, color=theme.Colors.TEXT),
                        ft.Text("Vérifiez votre connexion internet puis réessayez.",
                                size=13, color=theme.Colors.TEXT_MUTED,
                                text_align=ft.TextAlign.CENTER),
                        ft.Container(height=8),
                        theme.primary_button("Réessayer", icon=ft.Icons.REFRESH,
                                             width=220, on_click=lambda e: on_retry()),
                        ft.TextButton(
                            "Retour à l'accueil",
                            on_click=lambda e: page.go(home_route(page)),
                            style=ft.ButtonStyle(color=theme.Colors.PRIMARY_ACTION),
                        ),
                    ],
                ),
            )
        ],
    )
