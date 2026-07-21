from urllib.parse import urlparse, parse_qs

import flet as ft

from components import theme
from components.app_shell import home_route


def build_auth_callback_view(page: ft.Page) -> ft.View:
    """Page affichée après un clic sur un lien envoyé par email par Supabase
    (confirmation d'inscription, réinitialisation de mot de passe…).

    Supabase renvoie ces liens avec les informations dans le FRAGMENT d'URL
    (#access_token=... ou #error=...), qu'un petit script dans assets/index.html
    convertit en paramètres de requête classiques (?status=...) AVANT que
    Flet ne construise quoi que ce soit — voir ce fichier pour le détail.
    Cette page se contente d'afficher un résultat clair, à notre image,
    au lieu de l'erreur brute du navigateur ou d'une redirection vers un
    localhost qui n'existe pas une fois l'app déployée.
    """
    # On parse `page.route` nous-mêmes (plutôt que `page.query`, dont la mise
    # à jour interne est asynchrone et pas garantie prête à ce stade précis)
    # pour lire les paramètres de façon fiable, quel que soit le moment.
    parsed = urlparse(page.route)
    q = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    status = q.get("status")

    if status == "ok":
        access_token = q.get("at")
        refresh_token = q.get("rt")
        restored = False
        if access_token and refresh_token:
            try:
                restored = page.db.restore_session(access_token, refresh_token)
            except Exception:
                restored = False

        if restored:
            icon = ft.Icons.CHECK_CIRCLE_ROUNDED
            title = "Email confirmé !"
            message = "Votre adresse a été vérifiée avec succès. Vous êtes maintenant connecté(e)."
            primary_label = "Accéder à mon espace"
            primary_route = home_route(page)
        else:
            icon = ft.Icons.CHECK_CIRCLE_ROUNDED
            title = "Email confirmé !"
            message = "Votre adresse a été vérifiée avec succès. Vous pouvez maintenant vous connecter."
            primary_label = "Se connecter"
            primary_route = "/login"
        icon_color = theme.Colors.SUCCESS
    else:
        icon = ft.Icons.ERROR_ROUNDED
        title = "Lien invalide ou expiré"
        message = (
            (q.get("msg") or "Ce lien n'est plus valide.")
            + " Réinscrivez-vous ou reconnectez-vous pour recevoir un nouveau lien."
        )
        primary_label = "Retour à la connexion"
        primary_route = "/login"
        icon_color = theme.Colors.ERROR

    return ft.View(
        route=page.route,
        bgcolor="#0A0F1A",
        padding=0,
        appbar=theme.auth_appbar(page, route_back="/"),
        controls=[
            theme.glass_auth_background(
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        theme.glass_card(
                            width=380,
                            padding=36,
                            content=ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=10,
                                controls=[
                                    theme.gradient_icon_badge(ft.Icons.SCHOOL_ROUNDED),
                                    ft.Container(height=6),
                                    ft.Icon(icon, size=52, color=icon_color),
                                    ft.Text(title, size=20, weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER),
                                    ft.Text(message, size=13, text_align=ft.TextAlign.CENTER,
                                            color=ft.Colors.with_opacity(0.65, ft.Colors.WHITE)),
                                    ft.Container(height=10),
                                    theme.gradient_button(
                                        primary_label,
                                        icon=ft.Icons.ARROW_FORWARD,
                                        width=260,
                                        on_click=lambda e: page.go(primary_route),
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
            )
        ],
    )
