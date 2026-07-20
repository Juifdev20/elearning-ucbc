import flet as ft

from components import theme


def build_forgot_password_view(page: ft.Page) -> ft.View:
    """Écran de demande de réinitialisation du mot de passe (email Supabase)."""
    email_field = theme.glass_text_field("Email", icon=ft.Icons.EMAIL_OUTLINED, autofocus=True)
    info_text = ft.Text("", size=13)
    loading = ft.ProgressRing(visible=False, width=20, height=20, stroke_width=2, color=ft.Colors.WHITE)

    def send_reset(e):
        info_text.value = ""
        if not email_field.value:
            info_text.value = "Veuillez saisir votre email."
            info_text.color = "#FCA5A5"
            page.update()
            return

        loading.visible = True
        send_btn.disabled = True
        page.update()

        try:
            page.db.reset_password(email_field.value.strip())
            info_text.value = "Si un compte existe, un email de réinitialisation vient d'être envoyé."
            info_text.color = "#86EFAC"
        except Exception:
            # On reste volontairement discret pour ne pas révéler l'existence d'un compte.
            info_text.value = "Si un compte existe, un email de réinitialisation vient d'être envoyé."
            info_text.color = "#86EFAC"
        finally:
            loading.visible = False
            send_btn.disabled = False
            page.update()

    send_btn = theme.gradient_button("Envoyer le lien", icon=ft.Icons.SEND_OUTLINED, width=280, on_click=send_reset)

    return ft.View(
        route="/forgot-password",
        bgcolor="#0A0F1A",
        padding=0,
        appbar=theme.auth_appbar(page, route_back="/login"),
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
                                    theme.gradient_icon_badge(ft.Icons.LOCK_RESET_ROUNDED),
                                    ft.Container(height=10),
                                    ft.Text("Mot de passe oublié", size=22, weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.WHITE),
                                    ft.Text("Recevez un lien de réinitialisation par email.", size=13,
                                            color=ft.Colors.with_opacity(0.6, ft.Colors.WHITE)),
                                    ft.Container(height=18),
                                    email_field,
                                    info_text,
                                    ft.Container(height=6),
                                    ft.Row([loading, send_btn], alignment=ft.MainAxisAlignment.CENTER),
                                    ft.Container(height=6),
                                    ft.TextButton(
                                        "← Retour à la connexion",
                                        on_click=lambda e: page.go("/login"),
                                        style=ft.ButtonStyle(color="#A78BFA"),
                                    ),
                                ]
                            ),
                        ),
                    ],
                ),
            )
        ],
    )
