import flet as ft

from services.supabase_service import db
from components import theme


def build_signup_view(page: ft.Page) -> ft.View:
    name_field = theme.text_field("Nom complet", icon=ft.Icons.PERSON_OUTLINE)
    email_field = theme.text_field("Email", icon=ft.Icons.EMAIL_OUTLINED)
    password_field = theme.text_field("Mot de passe (min. 6 caractères)", password=True, icon=ft.Icons.LOCK_OUTLINE)
    error_text = ft.Text("", color=theme.Colors.ERROR, size=13)
    success_text = ft.Text("", color=theme.Colors.SUCCESS, size=13)
    loading = ft.ProgressRing(visible=False, width=20, height=20, stroke_width=2, color=theme.Colors.PRIMARY_ACTION)

    def do_signup(e):
        error_text.value = ""
        success_text.value = ""
        if not name_field.value or not email_field.value or not password_field.value:
            error_text.value = "Veuillez remplir tous les champs."
            page.update()
            return
        if len(password_field.value) < 6:
            error_text.value = "Le mot de passe doit contenir au moins 6 caractères."
            page.update()
            return

        loading.visible = True
        signup_btn.disabled = True
        page.update()

        try:
            db.sign_up(email_field.value.strip(), password_field.value, name_field.value.strip())
            success_text.value = "Compte créé ! Vous pouvez vous connecter."
        except Exception:
            error_text.value = "Erreur lors de l'inscription. Cet email est peut-être déjà utilisé."
        finally:
            loading.visible = False
            signup_btn.disabled = False
            page.update()

    signup_btn = theme.primary_button("Créer mon compte", icon=ft.Icons.PERSON_ADD_ALT_1, on_click=do_signup)

    return ft.View(
        route="/signup",
        bgcolor=theme.Colors.BG,
        padding=0,
        controls=[
            theme.auth_background(
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        theme.brand_logo(size=64),
                        ft.Container(height=8),
                        ft.Text("Créer un compte", size=24, weight=ft.FontWeight.BOLD, color=theme.Colors.PRIMARY),
                        ft.Container(height=16),
                        theme.card(
                            width=320,
                            padding=24,
                            content=ft.Column(
                                controls=[
                                    name_field,
                                    email_field,
                                    password_field,
                                    error_text,
                                    success_text,
                                    ft.Row([loading, signup_btn], alignment=ft.MainAxisAlignment.CENTER),
                                    ft.Container(height=8),
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        controls=[
                                            theme.body("Déjà un compte ?", muted=True),
                                            ft.TextButton(
                                                "Se connecter",
                                                on_click=lambda e: page.go("/login"),
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
