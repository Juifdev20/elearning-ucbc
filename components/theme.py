"""
Design system centralisé de l'application E-Learning UCBC.

Toute la charte graphique (couleurs, rayons, ombres, styles de texte et
composants réutilisables) est définie ici. Les vues doivent importer depuis
ce module plutôt que de coder des couleurs en dur, pour garantir une identité
visuelle cohérente et facile à faire évoluer.

Style inspiré des dashboards SaaS modernes : icônes sur fonds pastel,
cartes statistiques, carte "héro" en dégradé, sidebar avec item actif teinté.
"""
import flet as ft


# ---------------------------------------------------------------------------
# MODE SOMBRE — préférence PAR SESSION (pas un réglage global partagé par
# tous les visiteurs : l'app est servie en web à plusieurs utilisateurs en
# parallèle depuis le même process, donc une préférence "dark mode" mutée sur
# une classe partagée s'appliquerait à tout le monde en même temps).
#
# Le nécessaire est stocké sur `page.dark_mode` (voir set_dark ci-dessous).
# Pour que `Colors.BG` etc. restent lisibles PARTOUT dans le code sans y
# passer `page` explicitement (des centaines d'appels dans tout le projet),
# on s'appuie sur `ft.context.page` : le mécanisme officiel de Flet qui donne
# accès à la page de la session EN COURS depuis n'importe où, quel que soit
# le thread qui exécute le code (Flet réinjecte ce contexte à chaque
# évènement dispatché — page.go(), clic de bouton, etc. — via son propre
# `run_task`/`run_thread`, y compris entre plusieurs utilisateurs connectés
# en même temps).
# ---------------------------------------------------------------------------
_LIGHT = {
    "PRIMARY": "#1E3A8A",
    "PRIMARY_ACTION": "#2563EB",
    "BLUE_LIGHT": "#EFF6FF",
    "BLUE_LIGHT_2": "#DBEAFE",
    "TEXT": "#111827",
    "TEXT_MUTED": "#6B7280",
    "BG": "#F9FAFB",
    "SURFACE": "#FFFFFF",
    "BORDER": "#E5E7EB",
}
# Palette sombre façon "InuaAfya" : fond quasi-noir teinté de bleu,
# cartes à peine plus claires cerclées d'une fine bordure (pas d'ombre),
# accents VIFS qui ressortent sur le noir.
_DARK = {
    "PRIMARY": "#60A5FA",         # bleu clair vif : titres, logo, nom coloré
    "PRIMARY_ACTION": "#3B82F6",  # bleu vif : actions, item actif, liens
    "BLUE_LIGHT": "#0F1B33",
    "BLUE_LIGHT_2": "#16294A",
    "TEXT": "#F8FAFC",
    "TEXT_MUTED": "#8A94A6",
    "BG": "#0A0F1A",              # quasi-noir teinté de bleu
    "SURFACE": "#0F1626",         # cartes : à peine plus claires que le fond
    "BORDER": "#1E293B",          # fine bordure visible sur les cartes
}

# Bleus de marque FIXES (hero, logo) : restent identiques dans les deux modes,
# car ils portent du texte blanc.
BRAND_BLUE_DARK = "#1E3A8A"
BRAND_BLUE = "#2563EB"


def is_dark(page: ft.Page = None) -> bool:
    """Préférence sombre/clair de LA session courante (ou de `page` si fourni)."""
    p = page or ft.context.page
    return bool(getattr(p, "dark_mode", False)) if p is not None else False


def set_dark(page: ft.Page, on: bool):
    """Change la préférence sombre/clair de CETTE session uniquement."""
    page.dark_mode = on


class _ColorsMeta(type):
    """Résout dynamiquement PRIMARY/BG/TEXT/... selon le mode sombre de la
    session en cours à chaque accès (`Colors.BG`), au lieu de muter des
    attributs de classe partagés par tout le monde."""

    def __getattr__(cls, name):
        palette = _DARK if is_dark() else _LIGHT
        if name in palette:
            return palette[name]
        raise AttributeError(f"'Colors' n'a pas d'attribut {name!r}")


# ---------------------------------------------------------------------------
# PALETTE (charte imposée — voir PROMPT_CLAUDE_CODE.md §2)
# ---------------------------------------------------------------------------
class Colors(metaclass=_ColorsMeta):
    # Accents (identiques dans les deux modes)
    SUCCESS = "#16A34A"          # progression / réussite (vert)
    CERT = "#F59E0B"             # certification / brevet (or-ambre)
    ERROR = "#DC2626"            # erreur / alerte
    PURPLE = "#7C3AED"           # accent secondaire (stats, variété visuelle)
    TEAL = "#0D9488"             # accent secondaire (stats, variété visuelle)

    # PRIMARY, PRIMARY_ACTION, BLUE_LIGHT, BLUE_LIGHT_2, TEXT, TEXT_MUTED,
    # BG, SURFACE, BORDER : PAS définis ici — résolus dynamiquement par
    # `_ColorsMeta.__getattr__` ci-dessus, à partir de `_LIGHT`/`_DARK`.


def tint(color: str, opacity: float = 0.12) -> str:
    """Version pastel d'une couleur (pour fonds d'icônes, badges…).

    En mode sombre, l'opacité est légèrement renforcée pour que les fonds
    teintés restent bien visibles sur le noir.
    """
    if is_dark():
        opacity = min(opacity + 0.06, 1.0)
    return ft.Colors.with_opacity(opacity, color)


# ---------------------------------------------------------------------------
# GÉOMÉTRIE
# ---------------------------------------------------------------------------
RADIUS_CARD = 16
RADIUS_INPUT = 10
RADIUS_BADGE = 20  # chips arrondis façon pilule

# Largeur en dessous de laquelle on bascule en navigation mobile (barre du bas).
MOBILE_BREAKPOINT = 840


def card_shadow() -> ft.BoxShadow:
    """Ombre légère et douce commune à toutes les cartes (mode clair)."""
    return ft.BoxShadow(blur_radius=16, offset=ft.Offset(0, 4),
                        color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK))


def card_decor():
    """(shadow, border) selon le mode.

    Clair  : ombre douce, pas de bordure.
    Sombre : pas d'ombre, fine bordure (style InuaAfya).
    """
    if is_dark():
        return None, ft.border.all(1, Colors.BORDER)
    return card_shadow(), None


def brand_gradient() -> ft.LinearGradient:
    """Dégradé bleu de marque (cartes héro, en-têtes).

    Utilise les bleus FIXES (et non Colors.*) car ces surfaces portent du
    texte blanc : elles doivent rester identiques en mode sombre.
    """
    return ft.LinearGradient(
        begin=ft.alignment.top_left,
        end=ft.alignment.bottom_right,
        colors=[BRAND_BLUE_DARK, BRAND_BLUE],
    )


# ---------------------------------------------------------------------------
# THÈME GLOBAL FLET
# ---------------------------------------------------------------------------
def app_theme() -> ft.Theme:
    """Thème Flet appliqué à toute l'application (seed = bleu de marque)."""
    return ft.Theme(color_scheme_seed=Colors.PRIMARY)


# ---------------------------------------------------------------------------
# HELPERS DE TEXTE (hiérarchie typographique imposée : 28/22/18/16px)
# ---------------------------------------------------------------------------
def greeting(prefix: str, name: str, suffix: str = " 👋") -> ft.Text:
    """Grande salutation avec le nom en couleur d'accent (ex: Bonjour, *Eliana* 👋)."""
    return ft.Text(
        size=28,
        weight=ft.FontWeight.BOLD,
        spans=[
            ft.TextSpan(prefix, ft.TextStyle(color=Colors.TEXT)),
            ft.TextSpan(name, ft.TextStyle(color=Colors.PRIMARY_ACTION)),
            ft.TextSpan(suffix, ft.TextStyle(color=Colors.TEXT)),
        ],
    )


def page_title(text: str) -> ft.Text:
    return ft.Text(text, size=22, weight=ft.FontWeight.BOLD, color=Colors.TEXT)


def section_title(text: str) -> ft.Text:
    return ft.Text(text, size=18, weight=ft.FontWeight.BOLD, color=Colors.TEXT)


def subtitle(text: str) -> ft.Text:
    return ft.Text(text, size=16, weight=ft.FontWeight.W_600, color=Colors.TEXT)


def body(text: str, muted: bool = False) -> ft.Text:
    return ft.Text(text, size=13, color=Colors.TEXT_MUTED if muted else Colors.TEXT)


def overline(text: str, color: str = None) -> ft.Text:
    """Petit libellé en majuscules espacées (au-dessus d'une valeur)."""
    return ft.Text(text.upper(), size=10, weight=ft.FontWeight.W_700,
                   color=color or Colors.TEXT_MUTED)


# ---------------------------------------------------------------------------
# HELPERS DE COMPOSANTS
# ---------------------------------------------------------------------------
def card(content: ft.Control, padding: int = 16, bgcolor: str = None, **kwargs) -> ft.Container:
    """Carte standard : coins arrondis ; ombre douce en clair,
    fine bordure sans ombre en sombre. `bgcolor` peut être surchargé
    (ex : mettre en évidence la ligne de l'utilisateur courant)."""
    shadow, border = card_decor()
    return ft.Container(
        padding=padding,
        bgcolor=bgcolor or Colors.SURFACE,
        border_radius=RADIUS_CARD,
        shadow=shadow,
        border=border,
        content=content,
        **kwargs,
    )


def tinted_icon(icon, color: str, size: int = 22, box: int = 44,
                radius: int = 12) -> ft.Container:
    """Icône colorée dans un carré arrondi pastel (signature du design)."""
    return ft.Container(
        width=box,
        height=box,
        border_radius=radius,
        bgcolor=tint(color),
        alignment=ft.alignment.center,
        content=ft.Icon(icon, color=color, size=size),
    )


def stat_card(icon, label: str, value, color: str, **kwargs) -> ft.Container:
    """Carte statistique : icône pastel + libellé majuscule + valeur en gras."""
    return card(
        padding=18,
        content=ft.Row(
            spacing=14,
            controls=[
                tinted_icon(icon, color),
                ft.Column(
                    spacing=2,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        overline(label),
                        ft.Text(str(value), size=18, weight=ft.FontWeight.BOLD, color=Colors.TEXT),
                    ],
                ),
            ],
        ),
        **kwargs,
    )


def chip(text: str, color: str, filled: bool = False) -> ft.Container:
    """Pilule colorée (statut, catégorie…)."""
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=12, vertical=5),
        border_radius=RADIUS_BADGE,
        bgcolor=color if filled else tint(color, 0.14),
        content=ft.Text(text, size=11, weight=ft.FontWeight.W_600,
                        color=ft.Colors.WHITE if filled else color),
    )


COURSE_STATUS_LABELS = {
    "draft": "Brouillon",
    "pending_review": "En attente de validation",
    "published": "Publié",
    "rejected": "Rejeté",
}


def course_status_color(status: str) -> str:
    return {
        "draft": Colors.TEXT_MUTED,
        "pending_review": Colors.CERT,
        "published": Colors.SUCCESS,
        "rejected": Colors.ERROR,
    }.get(status, Colors.TEXT_MUTED)


def course_status_chip(status: str) -> ft.Container:
    """Pilule de statut de cours (workflow d'approbation), couleur/libellé cohérents partout."""
    return chip(COURSE_STATUS_LABELS.get(status, status), course_status_color(status))


def category_badge(text: str) -> ft.Container:
    """Badge de catégorie (bleu de marque pastel)."""
    return chip(text, Colors.PRIMARY_ACTION)


def progress_bar(value_percent: float, color: str = None) -> ft.ProgressBar:
    """Barre de progression normalisée (value_percent attendu en 0-100)."""
    return ft.ProgressBar(
        value=(value_percent or 0) / 100,
        color=color or Colors.SUCCESS,
        bgcolor=tint(Colors.TEXT_MUTED, 0.15),
        border_radius=6,
    )


def primary_button(text: str, on_click=None, icon=None, width=300) -> ft.ElevatedButton:
    """Bouton d'action principal (bleu vif)."""
    return ft.ElevatedButton(
        text=text,
        icon=icon,
        width=width,
        height=48,
        on_click=on_click,
        style=ft.ButtonStyle(
            bgcolor=Colors.PRIMARY_ACTION,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=RADIUS_INPUT),
            elevation=0,
        ),
    )


def white_button(text: str, on_click=None, icon=None) -> ft.ElevatedButton:
    """Bouton blanc à texte bleu — pour poser sur une carte héro en dégradé."""
    return ft.ElevatedButton(
        text=text,
        icon=icon,
        height=44,
        on_click=on_click,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.WHITE,
            color=BRAND_BLUE_DARK,  # fixe : posé sur carte héro, identique en sombre
            shape=ft.RoundedRectangleBorder(radius=RADIUS_INPUT),
            elevation=0,
        ),
    )


def text_field(label: str, password: bool = False, icon=None, autofocus: bool = False) -> ft.TextField:
    """Champ de formulaire stylé selon la charte (bordure arrondie, focus bleu)."""
    return ft.TextField(
        label=label,
        password=password,
        can_reveal_password=password,
        prefix_icon=icon,
        autofocus=autofocus,
        border_radius=RADIUS_INPUT,
        border_color=Colors.BORDER,
        focused_border_color=Colors.PRIMARY_ACTION,
        cursor_color=Colors.PRIMARY_ACTION,
        bgcolor=Colors.SURFACE,
    )


def branded_appbar(title: str, leading=None, actions: list | None = None) -> ft.AppBar:
    """AppBar de marque pour les écrans secondaires (détail cours, quiz…)."""
    return ft.AppBar(
        title=ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=Colors.PRIMARY),
        bgcolor=Colors.SURFACE,
        leading=leading,
        actions=actions or [],
    )


def auth_appbar(page: ft.Page, route_back: str = "/") -> ft.AppBar:
    """Barre transparente avec flèche retour, pour les écrans d'authentification
    (retour à la page d'accueil publique)."""
    return ft.AppBar(
        bgcolor=ft.Colors.TRANSPARENT,
        elevation=0,
        leading=ft.IconButton(
            ft.Icons.ARROW_BACK,
            icon_color=Colors.PRIMARY,
            tooltip="Retour à l'accueil",
            on_click=lambda e: page.go(route_back),
        ),
    )


def auth_background(content: ft.Control) -> ft.Container:
    """Fond dégradé doux pour les écrans d'authentification."""
    return ft.Container(
        expand=True,
        alignment=ft.alignment.center,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=[Colors.BLUE_LIGHT, Colors.BG],
        ),
        content=content,
    )


def bar_chart(data: list) -> ft.BarChart:
    """Graphique en barres générique : liste de {"title": str, "count": int}.

    Réutilisé par les pages "Vue d'ensemble" admin et formateur.
    """
    max_count = max((d["count"] for d in data), default=1) or 1
    colors = [Colors.PRIMARY_ACTION, Colors.PURPLE, Colors.TEAL, Colors.CERT, Colors.SUCCESS]

    groups = []
    labels = []
    for i, d in enumerate(data):
        groups.append(
            ft.BarChartGroup(
                x=i,
                bar_rods=[
                    ft.BarChartRod(
                        from_y=0,
                        to_y=d["count"],
                        width=28,
                        color=colors[i % len(colors)],
                        border_radius=6,
                        tooltip=f"{d['title']} : {d['count']}",
                    )
                ],
            )
        )
        short = d["title"] if len(d["title"]) <= 14 else d["title"][:12] + "…"
        labels.append(
            ft.ChartAxisLabel(
                value=i,
                label=ft.Container(
                    padding=ft.padding.only(top=6),
                    content=ft.Text(short, size=10, color=Colors.TEXT_MUTED),
                ),
            )
        )

    return ft.BarChart(
        bar_groups=groups,
        border=ft.border.all(1, ft.Colors.TRANSPARENT),
        left_axis=ft.ChartAxis(labels_size=30, title_size=0),
        bottom_axis=ft.ChartAxis(labels=labels, labels_size=34),
        horizontal_grid_lines=ft.ChartGridLines(
            interval=max(1, round(max_count / 4)), color=Colors.BORDER, width=1),
        max_y=max_count * 1.2 if max_count else 5,
        interactive=True,
        expand=True,
    )


def brand_logo(size: int = 64) -> ft.Container:
    """Logo de marque : chapeau d'étudiant blanc sur carré dégradé."""
    return ft.Container(
        width=size,
        height=size,
        border_radius=size // 3,
        gradient=brand_gradient(),
        alignment=ft.alignment.center,
        content=ft.Icon(ft.Icons.SCHOOL_ROUNDED, size=int(size * 0.55), color=ft.Colors.WHITE),
    )
