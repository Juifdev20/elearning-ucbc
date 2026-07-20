import flet as ft

from components import theme
from components.app_shell import home_route
from services.supabase_service import ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY


def build_login_view(page: ft.Page) -> ft.View:
    email_field = theme.glass_text_field("Email", icon=ft.Icons.EMAIL_OUTLINED, autofocus=True)
    password_field = theme.glass_text_field("Mot de passe", password=True, icon=ft.Icons.LOCK_OUTLINE)
    error_text = ft.Text("", color="#FCA5A5", size=13)
    loading = ft.ProgressRing(visible=False, width=20, height=20, stroke_width=2, color=ft.Colors.WHITE)

    def do_login(e):
        error_text.value = ""
        if not email_field.value or not password_field.value:
            error_text.value = "Veuillez remplir tous les champs."
            page.update()
            return

        loading.visible = True
        login_btn.content.controls[-1].value = "Connexion…"
        page.update()

        try:
            result = page.db.sign_in(email_field.value.strip(), password_field.value)
            # "Se souvenir de moi" (comme Facebook/WhatsApp) : jetons enregistrés
            # sur CET appareil pour reconnecter automatiquement la prochaine fois.
            if result.session:
                try:
                    page.client_storage.set(ACCESS_TOKEN_KEY, result.session.access_token)
                    page.client_storage.set(REFRESH_TOKEN_KEY, result.session.refresh_token)
                except Exception:
                    pass
            # Chaque rôle a sa propre interface d'accueil (étudiant, formateur, admin).
            page.go(home_route(page))
        except Exception:
            error_text.value = "Email ou mot de passe incorrect."
            loading.visible = False
            login_btn.content.controls[-1].value = "Se connecter"
            page.update()

    login_btn = theme.gradient_button("Se connecter", icon=ft.Icons.LOGIN, width=280, on_click=do_login)

    return ft.View(
        route="/login",
        bgcolor="#0A0F1A",
        padding=0,
        appbar=theme.auth_appbar(page),
        controls=[
            theme.glass_auth_background(
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        theme.glass_card(
                            width=340,
                            padding=32,
                            content=ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=6,
                                controls=[
                                    theme.gradient_icon_badge(ft.Icons.SCHOOL_ROUNDED),
                                    ft.Container(height=10),
                                    ft.Text("Bon retour", size=22, weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.WHITE),
                                    ft.Text("Connectez-vous pour continuer.", size=13,
                                            color=ft.Colors.with_opacity(0.6, ft.Colors.WHITE)),
                                    ft.Container(height=18),
                                    email_field,
                                    password_field,
                                    error_text,
                                    ft.Container(height=6),
                                    ft.Row([loading, login_btn], alignment=ft.MainAxisAlignment.CENTER),
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        controls=[
                                            ft.TextButton(
                                                "Mot de passe oublié ?",
                                                on_click=lambda e: page.go("/forgot-password"),
                                                style=ft.ButtonStyle(color="#A78BFA"),
                                            ),
                                        ],
                                    ),
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        controls=[
                                            ft.Text("Pas encore de compte ?", size=13,
                                                    color=ft.Colors.with_opacity(0.6, ft.Colors.WHITE)),
                                            ft.TextButton(
                                                "S'inscrire",
                                                on_click=lambda e: page.go("/signup"),
                                                style=ft.ButtonStyle(color="#A78BFA"),
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
            )
        ],
    )
