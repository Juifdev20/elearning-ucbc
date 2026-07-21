import flet as ft

from components import theme


def build_signup_view(page: ft.Page) -> ft.View:
    name_field = theme.glass_text_field("Nom complet", icon=ft.Icons.PERSON_OUTLINE)
    email_field = theme.glass_text_field("Email", icon=ft.Icons.EMAIL_OUTLINED)
    password_field = theme.glass_text_field("Mot de passe (min. 6 caractères)", password=True,
                                            icon=ft.Icons.LOCK_OUTLINE)
    error_text = ft.Text("", color="#FCA5A5", size=13)
    success_text = ft.Text("", color="#86EFAC", size=13)
    loading = ft.ProgressRing(visible=False, width=20, height=20, stroke_width=2, color=ft.Colors.WHITE)

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
            result = page.db.sign_up(email_field.value.strip(), password_field.value, name_field.value.strip())
            # Supabase exige par défaut la confirmation de l'email : tant que
            # ce n'est pas fait, `session` reste vide et la connexion échouera
            # ("email non confirmé") — prévenir tout de suite évite la
            # confusion ("email/mot de passe incorrect" alors que le compte
            # existe bel et bien).
            if result.session:
                success_text.value = "Compte créé ! Vous pouvez vous connecter."
            else:
                success_text.value = (
                    "Compte créé ! Vérifiez votre boîte mail (et les spams) pour confirmer "
                    "votre adresse AVANT de vous connecter."
                )
        except Exception:
            error_text.value = "Erreur lors de l'inscription. Cet email est peut-être déjà utilisé."
        finally:
            loading.visible = False
            signup_btn.disabled = False
            page.update()

    signup_btn = theme.gradient_button("Créer mon compte", icon=ft.Icons.PERSON_ADD_ALT_1,
                                       width=280, on_click=do_signup)

    return ft.View(
        route="/signup",
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
                                    theme.gradient_icon_badge(ft.Icons.PERSON_ADD_ALT_1_ROUNDED),
                                    ft.Container(height=10),
                                    ft.Text("Créer un compte", size=22, weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.WHITE),
                                    ft.Text("Rejoignez la plateforme en quelques secondes.", size=13,
                                            color=ft.Colors.with_opacity(0.6, ft.Colors.WHITE)),
                                    ft.Container(height=18),
                                    name_field,
                                    email_field,
                                    password_field,
                                    error_text,
                                    success_text,
                                    ft.Container(height=6),
                                    ft.Row([loading, signup_btn], alignment=ft.MainAxisAlignment.CENTER),
                                    ft.Container(height=6),
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        controls=[
                                            ft.Text("Déjà un compte ?", size=13,
                                                    color=ft.Colors.with_opacity(0.6, ft.Colors.WHITE)),
                                            ft.TextButton(
                                                "Se connecter",
                                                on_click=lambda e: page.go("/login"),
                                                style=ft.ButtonStyle(color="#A78BFA"),
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
