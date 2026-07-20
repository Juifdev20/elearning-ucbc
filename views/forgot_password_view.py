import flet as ft

from components import theme


def build_forgot_password_view(page: ft.Page) -> ft.View:
    """Écran de demande de réinitialisation du mot de passe (email Supabase)."""
    email_field = theme.text_field("Email", icon=ft.Icons.EMAIL_OUTLINED, autofocus=True)
    info_text = ft.Text("", size=13)
    loading = ft.ProgressRing(visible=False, width=20, height=20, stroke_width=2, color=theme.Colors.PRIMARY_ACTION)

    def send_reset(e):
        info_text.value = ""
        if not email_field.value:
            info_text.value = "Veuillez saisir votre email."
            info_text.color = theme.Colors.ERROR
            page.update()
            return

        loading.visible = True
        send_btn.disabled = True
        page.update()

        try:
            page.db.reset_password(email_field.value.strip())
            info_text.value = "Si un compte existe, un email de réinitialisation vient d'être envoyé."
            info_text.color = theme.Colors.SUCCESS
        except Exception:
            # On reste volontairement discret pour ne pas révéler l'existence d'un compte.
            info_text.value = "Si un compte existe, un email de réinitialisation vient d'être envoyé."
            info_text.color = theme.Colors.SUCCESS
        finally:
            loading.visible = False
            send_btn.disabled = False
            page.update()

    send_btn = theme.primary_button("Envoyer le lien", icon=ft.Icons.SEND_OUTLINED, width=240, on_click=send_reset)

    return ft.View(
        route="/forgot-password",
        bgcolor=theme.Colors.BG,
        padding=0,
        appbar=theme.auth_appbar(page, route_back="/login"),
        controls=[
            theme.auth_background(
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        theme.tinted_icon(ft.Icons.LOCK_RESET, theme.Colors.PRIMARY_ACTION,
                                          box=64, size=32, radius=18),
                        ft.Container(height=8),
                        ft.Text("Mot de passe oublié", size=22, weight=ft.FontWeight.BOLD, color=theme.Colors.PRIMARY),
                        theme.body("Recevez un lien de réinitialisation par email.", muted=True),
                        ft.Container(height=16),
                        theme.card(
                            width=320,
                            padding=24,
                            content=ft.Column(
                                controls=[
                                    email_field,
                                    info_text,
                                    ft.Row([loading, send_btn], alignment=ft.MainAxisAlignment.CENTER),
                                    ft.Container(height=8),
                                    ft.TextButton(
                                        "← Retour à la connexion",
                                        on_click=lambda e: page.go("/login"),
                                        style=ft.ButtonStyle(color=theme.Colors.PRIMARY_ACTION),
                                    ),
                                ]
                            ),
                        ),
                    ],
                ),
            )
        ],
    )
