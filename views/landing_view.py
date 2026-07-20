import asyncio
import os

import flet as ft

from components import theme
from components.app_shell import is_desktop

# Dossier (sous assets/) où déposer les photos des étudiants pour le
# carrousel du hero. Formats acceptés : jpg / jpeg / png / webp.
STUDENTS_ASSET_DIR = "landing/students"


def _list_student_images() -> list[str]:
    """Chemins (relatifs à assets/) des photos déposées par l'utilisateur.

    Liste vide si le dossier n'existe pas encore ou ne contient aucune image :
    le carrousel bascule alors sur des cartes décoratives en attendant.
    """
    abs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", STUDENTS_ASSET_DIR)
    if not os.path.isdir(abs_dir):
        return []
    exts = (".jpg", ".jpeg", ".png", ".webp")
    files = sorted(f for f in os.listdir(abs_dir) if f.lower().endswith(exts))
    return [f"{STUDENTS_ASSET_DIR}/{f}" for f in files]


def _nav_link(text: str, on_click) -> ft.TextButton:
    return ft.TextButton(
        text,
        on_click=on_click,
        style=ft.ButtonStyle(color=theme.Colors.TEXT_MUTED, overlay_color=ft.Colors.TRANSPARENT),
    )


def _header(page: ft.Page, desktop: bool, scroll_to) -> ft.Container:
    # Seuil PROPRE à cette barre de navigation (indépendant du seuil global
    # sidebar/bottom-nav de l'app) : entre 840 et ~980px, il y a assez de
    # place pour "desktop" (logo+texte, gros boutons) mais PAS assez pour en
    # plus les 3 liens de navigation — les cacher plutôt que risquer un
    # retour à la ligne qui casserait la barre sur 2-3 lignes.
    width = page.width or (page.window.width if hasattr(page, "window") else 0) or 1200
    show_nav_links = desktop and width >= 980

    brand_children = [theme.brand_logo(size=38)]
    if desktop:
        # Sur mobile, le nom de marque est retiré pour laisser la place aux
        # boutons d'action (éviter tout débordement horizontal du header).
        brand_children.append(
            ft.Text("E-Learning UCBC", size=16, weight=ft.FontWeight.BOLD, color=theme.Colors.PRIMARY)
        )
    brand = ft.Row(spacing=10, controls=brand_children)

    if desktop:
        actions = ft.Row(
            spacing=8,
            controls=[
                ft.TextButton(
                    "Se connecter",
                    on_click=lambda e: page.go("/login"),
                    style=ft.ButtonStyle(color=theme.Colors.PRIMARY_ACTION),
                ),
                theme.primary_button(
                    "S'inscrire", icon=ft.Icons.ARROW_FORWARD,
                    width=150,
                    on_click=lambda e: page.go("/signup"),
                ),
            ],
        )
    else:
        # Mobile : bouton "Se connecter" réduit à une icône (au lieu d'un
        # texte) pour laisser toute la place nécessaire à l'inscription,
        # sans jamais risquer de déborder même sur les très petits écrans.
        actions = ft.Row(
            spacing=4,
            controls=[
                ft.IconButton(
                    ft.Icons.LOGIN,
                    icon_color=theme.Colors.PRIMARY_ACTION,
                    tooltip="Se connecter",
                    on_click=lambda e: page.go("/login"),
                ),
                theme.primary_button(
                    "S'inscrire",
                    width=100,
                    on_click=lambda e: page.go("/signup"),
                ),
            ],
        )

    # Section centrale : les liens de nav (si assez de place), sinon un
    # simple espaceur — dans les deux cas elle absorbe tout l'espace
    # restant, ce qui garde logo à gauche et actions à droite SANS jamais
    # avoir besoin d'un retour à la ligne (donc jamais de 2e/3e ligne).
    middle_content = ft.Row(
        spacing=4,
        alignment=ft.MainAxisAlignment.CENTER,
        controls=[
            _nav_link("Fonctionnalités", lambda e: scroll_to("features")),
            _nav_link("Comment ça marche", lambda e: scroll_to("how")),
            _nav_link("Rôles", lambda e: scroll_to("roles")),
        ],
    ) if show_nav_links else None
    middle = ft.Container(expand=True, alignment=ft.alignment.center, content=middle_content)

    return ft.Container(
        padding=ft.padding.symmetric(horizontal=24 if desktop else 10, vertical=10),
        bgcolor=theme.Colors.SURFACE,
        border=ft.border.only(bottom=ft.BorderSide(1, theme.Colors.BORDER)),
        content=ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[brand, middle, actions],
        ),
    )


def _hero(page: ft.Page, desktop: bool) -> ft.Container:
    title = ft.Text(
        "Apprenez à votre rythme.\nObtenez vos certificats.",
        size=38 if desktop else 26,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
        text_align=ft.TextAlign.LEFT if desktop else ft.TextAlign.CENTER,
    )
    subtitle = ft.Text(
        "Une plateforme e-learning complète : cours structurés, évaluations, "
        "certificats et suivi de progression — pensée pour les étudiants, "
        "les formateurs et les administrateurs.",
        size=16,
        color=ft.Colors.with_opacity(0.9, ft.Colors.WHITE),
        text_align=ft.TextAlign.LEFT if desktop else ft.TextAlign.CENTER,
    )
    cta_row = ft.Row(
        alignment=ft.MainAxisAlignment.START if desktop else ft.MainAxisAlignment.CENTER,
        wrap=True,
        spacing=12,
        controls=[
            theme.white_button(
                "Créer un compte gratuitement", icon=ft.Icons.PERSON_ADD_ALT_1,
                on_click=lambda e: page.go("/signup"),
            ),
            ft.OutlinedButton(
                "Se connecter",
                icon=ft.Icons.LOGIN,
                on_click=lambda e: page.go("/login"),
                style=ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    side=ft.BorderSide(1, ft.Colors.WHITE),
                    shape=ft.RoundedRectangleBorder(radius=theme.RADIUS_INPUT),
                ),
            ),
        ],
    )
    trust_row = ft.Row(
        alignment=ft.MainAxisAlignment.START if desktop else ft.MainAxisAlignment.CENTER,
        wrap=True,
        spacing=10,
        controls=[
            theme.chip("🎓 Cours variés", ft.Colors.WHITE),
            theme.chip("🏆 Certificats reconnus", ft.Colors.WHITE),
            theme.chip("📱 Web, desktop & mobile", ft.Colors.WHITE),
        ],
    )

    text_col = ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.START if desktop else ft.CrossAxisAlignment.CENTER,
        spacing=16,
        controls=[title, subtitle, cta_row, ft.Container(height=4), trust_row],
    )

    illustration = ft.Container(
        width=220,
        height=220,
        border_radius=28,
        bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
        alignment=ft.alignment.center,
        content=ft.Icon(ft.Icons.SCHOOL_ROUNDED, size=110, color=ft.Colors.WHITE),
    )

    content = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[ft.Container(content=text_col, expand=True), illustration],
    ) if desktop else ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=24,
        controls=[illustration, text_col],
    )

    return ft.Container(
        padding=ft.padding.symmetric(horizontal=24 if desktop else 20, vertical=56 if desktop else 40),
        gradient=theme.brand_gradient(),
        content=content,
    )


def _students_marquee(page: ft.Page, desktop: bool) -> ft.Container:
    """Bande de photos des étudiants qui défile en boucle, en continu,
    de droite à gauche (sans à-coup : les deux jeux de cartes sont
    identiques, la ré-initialisation de position est instantanée donc
    invisible à l'œil)."""
    image_paths = _list_student_images()

    card_w = 150 if desktop else 112
    card_h = 190 if desktop else 142
    spacing = 16

    def _photo_card(src: str | None) -> ft.Container:
        photo = ft.Image(
            src=src,
            width=card_w,
            height=card_h,
            fit=ft.ImageFit.COVER,
            error_content=ft.Container(
                bgcolor=theme.tint(theme.Colors.PRIMARY_ACTION),
                alignment=ft.alignment.center,
                content=ft.Icon(ft.Icons.PERSON_ROUNDED, size=40, color=theme.Colors.PRIMARY_ACTION),
            ),
        ) if src else ft.Container(
            bgcolor=theme.tint(theme.Colors.PRIMARY_ACTION),
            alignment=ft.alignment.center,
            content=ft.Icon(ft.Icons.PERSON_ROUNDED, size=40, color=theme.Colors.PRIMARY_ACTION),
        )
        return ft.Container(
            width=card_w,
            height=card_h,
            border_radius=18,
            bgcolor=theme.Colors.SURFACE,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            shadow=theme.card_shadow(),
            content=photo,
        )

    # Cartes décoratives tant qu'aucune vraie photo n'a été déposée dans
    # assets/landing/students/ (voir le README de ce dossier).
    base = image_paths if image_paths else [None] * 6
    n = len(base)
    one_set_width = n * (card_w + spacing)

    # Rangée NATIVEMENT défilante (le même mécanisme que tous les
    # ft.Column(scroll=...) déjà utilisés partout ailleurs dans l'app —
    # contrairement à une position animée manuellement dans un Stack, celle-ci
    # est garantie de fonctionner). Le jeu de cartes est dupliqué deux fois :
    # une fois la moitié défilée, on saute instantanément (offset=0) au début
    # du second jeu, identique au premier — le bouclage est invisible.
    track = ft.Row(
        spacing=spacing,
        controls=[_photo_card(p) for p in base] + [_photo_card(p) for p in base],
        scroll=ft.ScrollMode.HIDDEN,
    )

    async def auto_scroll():
        offset = 0.0
        px_per_tick = 1.6
        while True:
            await asyncio.sleep(0.045)
            if page.route != "/":
                return
            offset += px_per_tick
            if offset >= one_set_width:
                offset = 0.0
            try:
                track.scroll_to(offset=offset, duration=0)
            except Exception:
                return  # la page a été fermée / la vue n'existe plus

    page.run_task(auto_scroll)

    viewport = ft.Container(
        height=card_h,
        content=track,
    )

    return ft.Container(
        key="students",
        padding=ft.padding.symmetric(horizontal=0, vertical=44 if desktop else 30),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            controls=[
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=24),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=4,
                        controls=[
                            theme.overline("Notre communauté", color=theme.Colors.PRIMARY_ACTION),
                            theme.page_title("Nos étudiants à l'UCBC"),
                        ],
                    ),
                ),
                ft.Container(height=18),
                viewport,
            ],
        ),
    )


def _feature_card(icon, color: str, title: str, desc: str) -> ft.Container:
    return ft.Container(
        col={"xs": 12, "sm": 6, "md": 4},
        content=theme.card(
            padding=20,
            content=ft.Column(
                spacing=10,
                controls=[
                    theme.tinted_icon(icon, color, box=48, size=22),
                    theme.subtitle(title),
                    theme.body(desc, muted=True),
                ],
            ),
        ),
    )


def _features_section(desktop: bool) -> ft.Container:
    cards = [
        _feature_card(ft.Icons.MENU_BOOK_ROUNDED, theme.Colors.PRIMARY_ACTION,
                      "Catalogue de cours varié",
                      "Des cours organisés par catégorie, avec leçons, vidéos et supports PDF téléchargeables."),
        _feature_card(ft.Icons.TRENDING_UP_ROUNDED, theme.Colors.SUCCESS,
                      "Suivi de progression",
                      "Chaque apprenant suit sa progression leçon par leçon, en temps réel."),
        _feature_card(ft.Icons.WORKSPACE_PREMIUM_ROUNDED, theme.Colors.CERT,
                      "Certificats téléchargeables",
                      "Un certificat est délivré automatiquement une fois le cours terminé et l'évaluation réussie."),
        _feature_card(ft.Icons.EMOJI_EVENTS_ROUNDED, theme.Colors.PURPLE,
                      "Classement & motivation",
                      "Un classement des apprenants les plus assidus pour stimuler l'engagement."),
        _feature_card(ft.Icons.CO_PRESENT_ROUNDED, theme.Colors.TEAL,
                      "Espace formateur complet",
                      "Créez vos cours, gérez vos apprenants et soumettez-les à validation avant publication."),
        _feature_card(ft.Icons.DEVICES_ROUNDED, theme.Colors.PRIMARY,
                      "Accessible partout",
                      "Interface responsive : web, ordinateur et mobile, avec une expérience adaptée à chaque écran."),
    ]
    return ft.Container(
        key="features",
        padding=ft.padding.symmetric(horizontal=24 if desktop else 16, vertical=48 if desktop else 32),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            controls=[
                theme.overline("Fonctionnalités", color=theme.Colors.PRIMARY_ACTION),
                theme.page_title("Tout ce qu'il faut pour enseigner et apprendre"),
                ft.Container(height=16),
                ft.ResponsiveRow(spacing=16, run_spacing=16, controls=cards),
            ],
        ),
    )


def _step(number: str, title: str, desc: str) -> ft.Container:
    return ft.Container(
        col={"xs": 12, "md": 4},
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.Container(
                    width=48, height=48, border_radius=24,
                    bgcolor=theme.Colors.PRIMARY_ACTION,
                    alignment=ft.alignment.center,
                    content=ft.Text(number, size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ),
                theme.subtitle(title),
                theme.body(desc, muted=True),
            ],
        ),
    )


def _how_it_works(desktop: bool) -> ft.Container:
    steps = [
        _step("1", "Créez votre compte", "Inscrivez-vous gratuitement en tant qu'apprenant en quelques secondes."),
        _step("2", "Suivez vos cours", "Parcourez les leçons à votre rythme : texte, vidéo et supports PDF."),
        _step("3", "Obtenez votre certificat", "Réussissez l'évaluation finale et téléchargez votre certificat."),
    ]
    return ft.Container(
        key="how",
        bgcolor=theme.Colors.SURFACE,
        padding=ft.padding.symmetric(horizontal=24 if desktop else 16, vertical=48 if desktop else 32),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            controls=[
                theme.overline("Comment ça marche", color=theme.Colors.PRIMARY_ACTION),
                theme.page_title("Trois étapes vers votre certification"),
                ft.Container(height=20),
                ft.ResponsiveRow(spacing=24, run_spacing=24, controls=steps,
                                 alignment=ft.MainAxisAlignment.CENTER),
            ],
        ),
    )


def _role_card(icon, color: str, role: str, desc: str, points: list[str]) -> ft.Container:
    return ft.Container(
        col={"xs": 12, "md": 4},
        content=theme.card(
            padding=22,
            content=ft.Column(
                spacing=10,
                controls=[
                    theme.tinted_icon(icon, color, box=48, size=22),
                    theme.subtitle(role),
                    theme.body(desc, muted=True),
                    ft.Container(height=4),
                    *[
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=color),
                                ft.Text(p, size=12, color=theme.Colors.TEXT, expand=True),
                            ],
                        )
                        for p in points
                    ],
                ],
            ),
        ),
    )


def _roles_section(desktop: bool) -> ft.Container:
    cards = [
        _role_card(ft.Icons.SCHOOL_OUTLINED, theme.Colors.PRIMARY_ACTION, "Étudiant",
                   "Une interface pensée pour apprendre sans distraction.",
                   ["Suivi des leçons et de la progression", "Certificats et classement", "Historique d'activité"]),
        _role_card(ft.Icons.CO_PRESENT_OUTLINED, theme.Colors.TEAL, "Formateur",
                   "Tous les outils pour créer et gérer ses cours.",
                   ["Création de cours et de leçons", "Soumission pour validation", "Suivi de ses apprenants"]),
        _role_card(ft.Icons.ADMIN_PANEL_SETTINGS_OUTLINED, theme.Colors.PURPLE, "Administrateur",
                   "Le pilotage complet de la plateforme.",
                   ["Validation des cours soumis", "Gestion des utilisateurs et rôles", "Statistiques globales"]),
    ]
    return ft.Container(
        key="roles",
        padding=ft.padding.symmetric(horizontal=24 if desktop else 16, vertical=48 if desktop else 32),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            controls=[
                theme.overline("Rôles", color=theme.Colors.PRIMARY_ACTION),
                theme.page_title("Une interface dédiée à chaque rôle"),
                ft.Container(height=16),
                ft.ResponsiveRow(spacing=16, run_spacing=16, controls=cards),
            ],
        ),
    )


def _cta_banner(page: ft.Page, desktop: bool) -> ft.Container:
    return ft.Container(
        margin=ft.margin.symmetric(horizontal=24 if desktop else 16, vertical=8),
        padding=ft.padding.symmetric(horizontal=32, vertical=40),
        border_radius=theme.RADIUS_CARD,
        gradient=theme.brand_gradient(),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=14,
            controls=[
                ft.Text("Prêt à commencer votre apprentissage ?", size=22 if desktop else 18,
                        weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER),
                ft.Text("Rejoignez la plateforme dès aujourd'hui, c'est gratuit.", size=13,
                        color=ft.Colors.with_opacity(0.9, ft.Colors.WHITE), text_align=ft.TextAlign.CENTER),
                theme.white_button(
                    "Créer un compte", icon=ft.Icons.ARROW_FORWARD,
                    on_click=lambda e: page.go("/signup"),
                ),
            ],
        ),
    )


def _footer(page: ft.Page) -> ft.Container:
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=24, vertical=24),
        bgcolor=theme.Colors.SURFACE,
        border=ft.border.only(top=ft.BorderSide(1, theme.Colors.BORDER)),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            controls=[
                ft.Row(
                    spacing=8,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        theme.brand_logo(size=28),
                        ft.Text("E-Learning UCBC", size=13, weight=ft.FontWeight.BOLD, color=theme.Colors.PRIMARY),
                    ],
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=4,
                    controls=[
                        ft.TextButton("Se connecter", on_click=lambda e: page.go("/login"),
                                     style=ft.ButtonStyle(color=theme.Colors.TEXT_MUTED)),
                        ft.Text("·", color=theme.Colors.TEXT_MUTED),
                        ft.TextButton("S'inscrire", on_click=lambda e: page.go("/signup"),
                                     style=ft.ButtonStyle(color=theme.Colors.TEXT_MUTED)),
                    ],
                ),
                theme.body("© 2026 E-Learning UCBC — Tous droits réservés.", muted=True),
            ],
        ),
    )


def build_landing_view(page: ft.Page) -> ft.View:
    """Page d'accueil publique (marketing) : présente la plateforme et
    dirige vers connexion / inscription. Adaptative mobile ↔ desktop."""
    desktop = is_desktop(page)

    scroll_col = ft.Column(
        spacing=0,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        controls=[
            _hero(page, desktop),
            _students_marquee(page, desktop),
            _features_section(desktop),
            _how_it_works(desktop),
            _roles_section(desktop),
            _cta_banner(page, desktop),
            _footer(page),
        ],
    )

    def scroll_to(key: str):
        scroll_col.scroll_to(key=key, duration=400, curve=ft.AnimationCurve.EASE_IN_OUT)

    return ft.View(
        route="/",
        bgcolor=theme.Colors.BG,
        padding=0,
        controls=[_header(page, desktop, scroll_to), scroll_col],
    )
