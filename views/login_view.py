import flet as ft

from components import theme
from components.app_shell import home_route


def build_login_view(page: ft.Page) -> ft.View:
    email_field = theme.text_field("Email", icon=ft.Icons.EMAIL_OUTLINED, autofocus=True)
    password_field = theme.text_field("Mot de passe", password=True, icon=ft.Icons.LOCK_OUTLINE)
    error_text = ft.Text("", color=theme.Colors.ERROR, size=13)
    loading = ft.ProgressRing(visible=False, width=20, height=20, stroke_width=2, color=theme.Colors.PRIMARY_ACTION)

    def do_login(e):
        error_text.value = ""
        if not email_field.value or not password_field.value:
            error_text.value = "Veuillez remplir tous les champs."
            page.update()
            return

        loading.visible = True
        login_btn.disabled = True
        page.update()

        try:
            page.db.sign_in(email_field.value.strip(), password_field.value)
            # Chaque rôle a sa propre interface d'accueil (étudiant, formateur, admin).
            page.go(home_route(page))
        except Exception:
            error_text.value = "Email ou mot de passe incorrect."
            loading.visible = False
            login_btn.disabled = False
            page.update()

    login_btn = theme.primary_button("Se connecter", icon=ft.Icons.LOGIN, width=240, on_click=do_login)

    return ft.View(
        route="/login",
        bgcolor=theme.Colors.BG,
        padding=0,
        appbar=theme.auth_appbar(page),
        controls=[
            theme.auth_background(
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        theme.brand_logo(size=72),
                        ft.Container(height=8),
                        ft.Text("E-Learning UCBC", size=26, weight=ft.FontWeight.BOLD, color=theme.Colors.PRIMARY),
                        theme.body("Apprenez à votre rythme", muted=True),
                        ft.Container(height=20),
                        theme.card(
                            width=320,
                            padding=24,
                            content=ft.Column(
                                controls=[
                                    email_field,
                                    password_field,
                                    error_text,
                                    ft.Row([loading, login_btn], alignment=ft.MainAxisAlignment.CENTER),
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        controls=[
                                            ft.TextButton(
                                                "Mot de passe oublié ?",
                                                on_click=lambda e: page.go("/forgot-password"),
                                                style=ft.ButtonStyle(color=theme.Colors.PRIMARY_ACTION),
                                            ),
                                        ],
                                    ),
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        controls=[
                                            theme.body("Pas encore de compte ?", muted=True),
                                            ft.TextButton(
                                                "S'inscrire",
                                                on_click=lambda e: page.go("/signup"),
                                                style=ft.ButtonStyle(color=theme.Colors.PRIMARY_ACTION),
                                            ),
                                        ],
                                    ),
                                ]
                            ),
                        ),
                    ],
                ),
            )
        ],
    )
