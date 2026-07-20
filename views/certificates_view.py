import flet as ft

from services.certificate_service import ensure_certificate
from components import theme
from components.app_shell import shell_view


def build_certificates_view(page: ft.Page) -> ft.View:
    """Onglet CERTIFICATS : tous les brevets obtenus par l'apprenant, téléchargeables."""
    profile = page.db.current_profile or {}
    full_name = profile.get("full_name", "") or "Apprenant"
    try:
        certificates = page.db.get_my_certificates()
    except Exception:
        certificates = []

    def download(course_title, course_id):
        def handler(e):
            score = 100
            try:
                s = page.db.get_best_passed_score(course_id)
                if s is not None:
                    score = s
            except Exception:
                pass
            page.launch_url(ensure_certificate(full_name, course_title, score,
                                               avatar_url=profile.get("avatar_url")))
        return handler

    def cert_card(cert):
        course_title = (cert.get("courses") or {}).get("title", "Cours")
        issued_at = (cert.get("issued_at") or "")[:10]
        return ft.Container(
            col={"xs": 12, "sm": 6, "md": 4},
            bgcolor=theme.Colors.SURFACE,
            border_radius=theme.RADIUS_CARD,
            shadow=theme.card_decor()[0],
            border=theme.card_decor()[1],
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Container(
                        height=90,
                        gradient=theme.brand_gradient(),
                        alignment=ft.alignment.center,
                        content=ft.Icon(ft.Icons.WORKSPACE_PREMIUM, size=42, color=ft.Colors.WHITE),
                    ),
                    ft.Container(
                        padding=16,
                        content=ft.Column(
                            spacing=8,
                            controls=[
                                theme.subtitle(course_title),
                                ft.Text(f"Délivré le {issued_at}", size=12,
                                        color=theme.Colors.TEXT_MUTED),
                                theme.primary_button(
                                    "Télécharger", icon=ft.Icons.DOWNLOAD, width=200,
                                    on_click=download(course_title, cert.get("course_id", "")),
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        )

    if certificates:
        grid = ft.ResponsiveRow(spacing=16, run_spacing=16,
                               controls=[cert_card(c) for c in certificates])
        content = grid
    else:
        content = theme.card(
            padding=32,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    theme.tinted_icon(ft.Icons.WORKSPACE_PREMIUM, theme.Colors.CERT,
                                      box=64, size=32, radius=18),
                    theme.subtitle("Aucun brevet obtenu pour l'instant"),
                    theme.body("Terminez un cours et réussissez le quiz final pour obtenir "
                               "votre premier certificat.", muted=True),
                    ft.Container(height=4),
                    theme.primary_button(
                        "Découvrir le catalogue", icon=ft.Icons.EXPLORE_OUTLINED, width=240,
                        on_click=lambda e: page.go("/dashboard"),
                    ),
                ],
            ),
        )

    body = ft.Container(
        padding=ft.padding.symmetric(horizontal=24, vertical=20),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                theme.page_title("Mes certificats"),
                theme.body(f"{len(certificates)} brevet(s) obtenu(s).", muted=True),
                ft.Container(height=16),
                content,
                ft.Container(height=20),
            ],
        ),
    )

    return shell_view(page, title="Mes certificats", body=body)
