"""
Coquille (shell) de navigation principale, responsive.

Desktop : sidebar latérale réductible (logo, items avec surbrillance,
Espace formateur si staff, déconnexion en bas) + topbar complète façon
dashboard SaaS : retour, refresh, recherche globale, langue, mode sombre,
notifications, pastille utilisateur.

Mobile : AppBar + barre de navigation en bas.

La bascule se fait automatiquement à partir de `page.width`
(seuil theme.MOBILE_BREAKPOINT).
"""
import flet as ft

from components import theme

# Chaque rôle a sa PROPRE navigation : un étudiant, un formateur et un
# administrateur ne voient pas les mêmes sections ni la même page d'accueil.
# (label, route, icône normale, icône sélectionnée)
STUDENT_NAV_ITEMS = [
    ("Tableau de bord", "/dashboard", ft.Icons.GRID_VIEW_OUTLINED, ft.Icons.GRID_VIEW_ROUNDED),
    ("Mes cours", "/my-courses", ft.Icons.MENU_BOOK_OUTLINED, ft.Icons.MENU_BOOK),
    ("Progression", "/progress", ft.Icons.TRENDING_UP_OUTLINED, ft.Icons.TRENDING_UP),
    ("Certificats", "/certificates", ft.Icons.WORKSPACE_PREMIUM_OUTLINED, ft.Icons.WORKSPACE_PREMIUM),
    ("Classement", "/leaderboard", ft.Icons.LEADERBOARD_OUTLINED, ft.Icons.LEADERBOARD),
    ("Mon profil", "/profile", ft.Icons.PERSON_OUTLINE, ft.Icons.PERSON),
]
INSTRUCTOR_NAV_ITEMS = [
    ("Vue d'ensemble", "/instructor", ft.Icons.GRID_VIEW_OUTLINED, ft.Icons.GRID_VIEW_ROUNDED),
    ("Mes cours", "/admin/courses", ft.Icons.MENU_BOOK_OUTLINED, ft.Icons.MENU_BOOK),
    ("Mes apprenants", "/instructor/students", ft.Icons.GROUP_OUTLINED, ft.Icons.GROUP),
    ("Mes certificats", "/instructor/certificates", ft.Icons.WORKSPACE_PREMIUM_OUTLINED, ft.Icons.WORKSPACE_PREMIUM),
    ("Mon profil", "/profile", ft.Icons.PERSON_OUTLINE, ft.Icons.PERSON),
]
ADMIN_NAV_ITEMS = [
    ("Vue d'ensemble", "/admin", ft.Icons.GRID_VIEW_OUTLINED, ft.Icons.GRID_VIEW_ROUNDED),
    ("Cours", "/admin/courses", ft.Icons.MENU_BOOK_OUTLINED, ft.Icons.MENU_BOOK),
    ("Cours à valider", "/admin/pending-courses", ft.Icons.PENDING_ACTIONS_OUTLINED, ft.Icons.PENDING_ACTIONS),
    ("Utilisateurs", "/admin/users", ft.Icons.MANAGE_ACCOUNTS_OUTLINED, ft.Icons.MANAGE_ACCOUNTS),
    ("Certificats", "/admin/certificates", ft.Icons.WORKSPACE_PREMIUM_OUTLINED, ft.Icons.WORKSPACE_PREMIUM),
    ("Catégories", "/admin/categories", ft.Icons.SELL_OUTLINED, ft.Icons.SELL),
    ("Annonces", "/admin/announcements", ft.Icons.CAMPAIGN_OUTLINED, ft.Icons.CAMPAIGN),
    ("Mon profil", "/profile", ft.Icons.PERSON_OUTLINE, ft.Icons.PERSON),
]


def get_nav_items(page: ft.Page) -> list:
    """Navigation propre au rôle de l'utilisateur courant."""
    role = (page.db.current_profile or {}).get("role", "student")
    if role == "admin":
        return ADMIN_NAV_ITEMS
    if role == "instructor":
        return INSTRUCTOR_NAV_ITEMS
    return STUDENT_NAV_ITEMS


def home_route(page: ft.Page) -> str:
    """Route d'accueil de l'utilisateur courant, selon son rôle."""
    items = get_nav_items(page)
    return items[0][1] if items else "/dashboard"


# Nombre de destinations affichées directement dans la barre du bas mobile.
# Au-delà, le surplus est rangé dans le tiroir latéral (☰) pour ne pas
# surcharger la barre — "Mon profil" (toujours le dernier item) reste
# visible directement, les items du milieu passent dans le tiroir.
MOBILE_BOTTOM_NAV_LIMIT = 4


def split_mobile_nav(nav_items: list) -> tuple[list, list]:
    """Découpe la navigation d'un rôle en (barre du bas, tiroir latéral).

    Si tout tient dans la limite, aucun tiroir n'est nécessaire.
    """
    if len(nav_items) <= MOBILE_BOTTOM_NAV_LIMIT:
        return nav_items, []
    keep = MOBILE_BOTTOM_NAV_LIMIT - 1  # une place réservée à "Mon profil"
    primary = nav_items[:keep] + [nav_items[-1]]
    secondary = nav_items[keep:-1]
    return primary, secondary


def _sidebar_subtitle(page: ft.Page) -> str:
    role = (page.db.current_profile or {}).get("role", "student")
    return {"admin": "ESPACE ADMINISTRATEUR", "instructor": "ESPACE FORMATEUR"}.get(
        role, "ESPACE APPRENANT")


SIDEBAR_WIDTH = 240
SIDEBAR_WIDTH_COLLAPSED = 78

# ---------------------------------------------------------------------------
# ÉTAT DU SHELL — attaché à CHAQUE `page` (jamais partagé entre sessions :
# l'app sert plusieurs utilisateurs en parallèle depuis le même process ;
# un état ici stocké au niveau du module mélangerait la sidebar réduite, la
# recherche ou l'historique de navigation d'un utilisateur avec un autre).
# ---------------------------------------------------------------------------
def _nav_state(page: ft.Page) -> dict:
    """Petit état de nav (sidebar réduite, historique) propre à cette session."""
    if not hasattr(page, "_shell_state"):
        page._shell_state = {"collapsed": False, "history": []}
    return page._shell_state


def _do_refresh(page: ft.Page):
    """Reconstruit la vue courante (dark mode, collapse, recherche…)."""
    refresh_fn = getattr(page, "refresh_view", None)
    if refresh_fn:
        refresh_fn()
    else:
        page.go(page.route)


def is_desktop(page: ft.Page) -> bool:
    """True si l'écran est assez large pour la sidebar latérale.

    Au tout premier rendu, `page.width` peut ne pas encore être mesuré (None) ;
    on se rabat alors sur la largeur de la fenêtre native pour éviter de
    construire à tort la navigation mobile sur un grand écran.
    """
    width = page.width
    if not width:
        try:
            width = page.window.width
        except Exception:
            width = 0
    return (width or 0) >= theme.MOBILE_BREAKPOINT


def _logout(page: ft.Page):
    def handler(e):
        page.db.sign_out()
        _nav_state(page)["history"].clear()
        page.go("/login")
    return handler


# ---------------------------------------------------------------------------
# SIDEBAR (desktop) — réductible
# ---------------------------------------------------------------------------
def _sidebar_item(page: ft.Page, label: str, route: str, icon, icon_selected,
                  active: bool, collapsed: bool, accent: str = None,
                  badge_count: int = 0) -> ft.Container:
    accent = accent or theme.Colors.PRIMARY_ACTION
    icon_widget = ft.Icon(icon_selected if active else icon, size=20,
                          color=accent if active else theme.Colors.TEXT_MUTED)
    badge = ft.Container(
        padding=ft.padding.symmetric(horizontal=6, vertical=1),
        border_radius=10,
        bgcolor=theme.Colors.ERROR,
        content=ft.Text(str(badge_count), size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
    ) if badge_count > 0 else None

    if collapsed:
        content = icon_widget
    else:
        row_controls = [
            icon_widget,
            ft.Text(label, size=13, expand=True,
                    weight=ft.FontWeight.W_700 if active else ft.FontWeight.W_500,
                    color=accent if active else theme.Colors.TEXT_MUTED),
        ]
        if badge:
            row_controls.append(badge)
        content = ft.Row(spacing=12, controls=row_controls)
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=0 if collapsed else 14, vertical=11),
        alignment=ft.alignment.center if collapsed else None,
        border_radius=10,
        bgcolor=theme.tint(accent, 0.10) if active else None,
        ink=True,
        tooltip=f"{label} ({badge_count})" if collapsed and badge_count else (label if collapsed else None),
        on_click=(lambda e: page.go(route)) if not active else None,
        content=content,
    )


def _sidebar(page: ft.Page, nav_items: list, active_index: int) -> ft.Container:
    collapsed = _nav_state(page)["collapsed"]

    # Badge de notification sur "Cours à valider" (nombre de cours en attente).
    pending_count = 0
    if page.db.is_admin():
        try:
            pending_count = len(page.db.get_pending_courses())
        except Exception:
            pending_count = 0

    items = [
        _sidebar_item(page, label, route, icon, sel, i == active_index, collapsed,
                     badge_count=pending_count if route == "/admin/pending-courses" else 0)
        for i, (label, route, icon, sel) in enumerate(nav_items)
    ]

    if collapsed:
        header = ft.Container(
            padding=ft.padding.only(top=4, bottom=18),
            alignment=ft.alignment.center,
            content=theme.brand_logo(size=40),
        )
        logout_row = ft.Container(
            padding=ft.padding.symmetric(vertical=11),
            alignment=ft.alignment.center,
            border_radius=10,
            ink=True,
            tooltip="Déconnexion",
            on_click=_logout(page),
            content=ft.Icon(ft.Icons.LOGOUT, size=20, color=theme.Colors.ERROR),
        )
    else:
        header = ft.Container(
            padding=ft.padding.only(left=6, top=4, bottom=18),
            content=ft.Row(
                spacing=12,
                controls=[
                    theme.brand_logo(size=42),
                    ft.Column(
                        spacing=0,
                        controls=[
                            ft.Text("E-LEARNING", size=14, weight=ft.FontWeight.W_800,
                                    color=theme.Colors.PRIMARY),
                            ft.Text(_sidebar_subtitle(page), size=9, weight=ft.FontWeight.W_600,
                                    color=theme.Colors.TEXT_MUTED),
                        ],
                    ),
                ],
            ),
        )
        logout_row = ft.Container(
            padding=ft.padding.symmetric(horizontal=14, vertical=11),
            border_radius=10,
            ink=True,
            on_click=_logout(page),
            content=ft.Row(
                spacing=12,
                controls=[
                    ft.Icon(ft.Icons.LOGOUT, size=20, color=theme.Colors.ERROR),
                    ft.Text("Déconnexion", size=13, weight=ft.FontWeight.W_600,
                            color=theme.Colors.ERROR),
                ],
            ),
        )

    return ft.Container(
        width=SIDEBAR_WIDTH_COLLAPSED if collapsed else SIDEBAR_WIDTH,
        bgcolor=theme.Colors.SURFACE,
        padding=ft.padding.symmetric(horizontal=10 if collapsed else 14, vertical=18),
        content=ft.Column(
            expand=True,
            controls=[
                header,
                *items,
                ft.Container(expand=True),  # pousse la déconnexion en bas
                ft.Divider(height=1, color=theme.Colors.BORDER),
                logout_row,
            ],
        ),
    )


def _notifications_dialog(page: ft.Page) -> ft.AlertDialog:
    """Dialogue de notifications, partagé desktop/mobile : dernières annonces."""
    try:
        announcements = page.db.get_announcements(limit=5)
    except Exception:
        announcements = []

    if announcements:
        rows = [
            ft.Container(
                padding=ft.padding.symmetric(vertical=8),
                content=ft.Column(
                    spacing=2,
                    controls=[
                        ft.Text(a.get("title", ""), size=13, weight=ft.FontWeight.W_700,
                                color=theme.Colors.TEXT),
                        ft.Text(a.get("message", ""), size=12, color=theme.Colors.TEXT_MUTED),
                    ],
                ),
            )
            for a in announcements
        ]
        content = ft.Column(tight=True, spacing=0, controls=rows, scroll=ft.ScrollMode.AUTO)
    else:
        content = ft.Text("Aucune nouvelle notification pour le moment. 🎉")

    dlg = ft.AlertDialog(
        title=ft.Row(
            spacing=10,
            controls=[
                theme.tinted_icon(ft.Icons.NOTIFICATIONS_OUTLINED,
                                  theme.Colors.PRIMARY_ACTION, box=36, size=18),
                ft.Text("Notifications", size=16, weight=ft.FontWeight.BOLD),
            ],
        ),
        content=ft.Container(width=340, height=320 if announcements else None, content=content),
        actions=[ft.TextButton("Fermer", on_click=lambda ev: page.close(dlg))],
    )
    return dlg


# ---------------------------------------------------------------------------
# TOPBAR (desktop) — retour, refresh, recherche, langue, dark, notifs, user
# ---------------------------------------------------------------------------
def _toolbar_icon(icon, tooltip, on_click, color=None) -> ft.IconButton:
    return ft.IconButton(
        icon=icon,
        icon_size=20,
        icon_color=color or theme.Colors.TEXT_MUTED,
        tooltip=tooltip,
        on_click=on_click,
    )


def _topbar(page: ft.Page, title: str, actions: list | None = None) -> ft.Container:
    profile = page.db.current_profile or {}
    full_name = profile.get("full_name", "Apprenant") or "Apprenant"
    role = (profile.get("role", "student") or "student").capitalize()
    nav_state = _nav_state(page)

    # --- Réduire / étendre la sidebar ---
    def toggle_sidebar(e):
        nav_state["collapsed"] = not nav_state["collapsed"]
        _do_refresh(page)

    collapse_btn = ft.Container(
        width=28,
        height=28,
        border_radius=30,
        border=ft.border.all(1, theme.Colors.BORDER),
        bgcolor=theme.Colors.SURFACE,
        alignment=ft.alignment.center,
        ink=True,
        tooltip="Étendre le menu" if nav_state["collapsed"] else "Réduire le menu",
        on_click=toggle_sidebar,
        content=ft.Icon(
            ft.Icons.CHEVRON_RIGHT if nav_state["collapsed"] else ft.Icons.CHEVRON_LEFT,
            size=16, color=theme.Colors.TEXT_MUTED,
        ),
    )

    # --- Retour ---
    def go_back(e):
        history = nav_state["history"]
        if len(history) >= 2:
            history.pop()               # retire la route courante
            page.go(history[-1])        # revient à la précédente
        else:
            page.go(home_route(page))

    # --- Refresh ---
    def do_refresh(e):
        _do_refresh(page)

    # --- Recherche globale : filtre le catalogue (étudiant) ou la liste
    # de cours (formateur/admin) selon le rôle de l'utilisateur courant.
    def submit_search(e):
        query = (e.control.value or "").strip()
        e.control.value = ""
        page.pending_search = query
        role = (page.db.current_profile or {}).get("role", "student")
        destination = "/admin/courses" if role in ("instructor", "admin") else "/dashboard"
        if page.route == destination:
            _do_refresh(page)
        else:
            page.go(destination)

    search = ft.Container(
        expand=True,
        padding=ft.padding.symmetric(horizontal=16),
        content=ft.TextField(
            hint_text="Rechercher…",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=30,
            height=42,
            content_padding=ft.padding.symmetric(horizontal=16, vertical=8),
            border_color=theme.Colors.BORDER,
            focused_border_color=theme.Colors.PRIMARY_ACTION,
            bgcolor=theme.Colors.BG,
            text_size=13,
            on_submit=submit_search,
        ),
    )

    # --- Langue ---
    def lang_soon(e):
        page.open(ft.SnackBar(ft.Text("🌍 L'interface anglaise arrive bientôt !")))

    language_menu = ft.PopupMenuButton(
        tooltip="Langue",
        content=ft.Container(
            padding=ft.padding.symmetric(horizontal=10, vertical=7),
            border_radius=8,
            border=ft.border.all(1, theme.Colors.BORDER),
            content=ft.Row(
                spacing=4,
                tight=True,
                controls=[
                    ft.Text("🇫🇷 FR", size=12, weight=ft.FontWeight.W_600,
                            color=theme.Colors.TEXT),
                    ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN, size=16,
                            color=theme.Colors.TEXT_MUTED),
                ],
            ),
        ),
        items=[
            ft.PopupMenuItem(text="🇫🇷 Français — actuel"),
            ft.PopupMenuItem(text="🇬🇧 English — bientôt", on_click=lang_soon),
        ],
    )

    # --- Mode sombre ---
    def toggle_dark(e):
        theme.set_dark(page, not theme.is_dark(page))
        page.theme_mode = ft.ThemeMode.DARK if theme.is_dark() else ft.ThemeMode.LIGHT
        page.bgcolor = theme.Colors.BG
        _do_refresh(page)

    # Anneau de surbrillance quand le mode sombre est actif (comme le modèle).
    dark_btn = ft.Container(
        border_radius=30,
        border=ft.border.all(1, theme.Colors.PRIMARY_ACTION) if theme.is_dark() else None,
        content=_toolbar_icon(
            ft.Icons.LIGHT_MODE_OUTLINED if theme.is_dark() else ft.Icons.DARK_MODE_OUTLINED,
            "Mode clair" if theme.is_dark() else "Mode sombre",
            toggle_dark,
            color=theme.Colors.PRIMARY_ACTION if theme.is_dark() else None,
        ),
    )

    # --- Notifications (annonces publiées par le formateur/admin) ---
    def show_notifications(e):
        page.open(_notifications_dialog(page))

    # --- Pastille utilisateur ---
    user_chip = ft.Container(
        padding=ft.padding.symmetric(horizontal=10, vertical=6),
        border_radius=30,
        ink=True,
        on_click=lambda e: page.go("/profile"),
        content=ft.Row(
            spacing=10,
            controls=[
                ft.CircleAvatar(
                    content=ft.Text(full_name[:1].upper(), size=14, weight=ft.FontWeight.BOLD),
                    radius=17,
                    bgcolor=theme.Colors.PRIMARY_ACTION,
                    color=ft.Colors.WHITE,
                ),
                ft.Column(
                    spacing=0,
                    controls=[
                        ft.Text(full_name, size=13, weight=ft.FontWeight.W_700,
                                color=theme.Colors.TEXT),
                        ft.Text(role, size=10, weight=ft.FontWeight.W_600,
                                color=theme.Colors.TEXT_MUTED),
                    ],
                ),
                ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN, size=16, color=theme.Colors.TEXT_MUTED),
            ],
        ),
    )

    return ft.Container(
        bgcolor=theme.Colors.SURFACE,
        padding=ft.padding.symmetric(horizontal=14, vertical=8),
        content=ft.Row(
            spacing=4,
            controls=[
                collapse_btn,
                _toolbar_icon(ft.Icons.ARROW_BACK, "Retour", go_back),
                _toolbar_icon(ft.Icons.REFRESH, "Actualiser", do_refresh),
                search,
                language_menu,
                dark_btn,
                _toolbar_icon(ft.Icons.NOTIFICATIONS_OUTLINED, "Notifications", show_notifications),
                *(actions or []),
                ft.Container(width=6),
                user_chip,
            ],
        ),
    )


# ---------------------------------------------------------------------------
# NAVIGATION MOBILE (barre du bas)
# ---------------------------------------------------------------------------
def _bottom_nav(page: ft.Page, nav_items: list, active_index: int | None) -> ft.NavigationBar:
    def on_change(e):
        route = nav_items[e.control.selected_index][1]
        if page.route != route:
            page.go(route)

    return ft.NavigationBar(
        selected_index=active_index,
        bgcolor=theme.Colors.SURFACE,
        indicator_color=theme.tint(theme.Colors.PRIMARY_ACTION, 0.14),
        on_change=on_change,
        destinations=[
            ft.NavigationBarDestination(label=label, icon=icon, selected_icon=sel)
            for (label, _route, icon, sel) in nav_items
        ],
    )


def _mobile_drawer(page: ft.Page, secondary_items: list) -> ft.AlertDialog:
    """Menu (☰) : options secondaires qui ne tiennent pas dans la barre du
    bas, pour ne pas la surcharger.

    Implémenté comme un AlertDialog (liste + déconnexion), PAS comme un
    ft.NavigationDrawer : ce dernier a un comportement peu fiable combiné à
    ft.View() dans Flet 0.28 (cf. issues officielles flet-dev/flet #5163 et
    discussion #2070 — le drawer ne s'ouvre/se ferme pas de façon fiable
    quand la vue est reconstruite à chaque navigation, ce qui est notre cas).
    Un AlertDialog ouvert/fermé via page.open()/page.close() est le mécanisme
    déjà utilisé (et fiable) partout ailleurs dans l'app (notifications,
    confirmations, etc.) — on réutilise volontairement ce même mécanisme
    plutôt que le contrôle dédié, justement parce qu'il est fiable."""
    profile = page.db.current_profile or {}
    full_name = profile.get("full_name", "Utilisateur") or "Utilisateur"

    def go_to(route):
        def handler(e):
            page.close(dlg)
            if page.route != route:
                page.go(route)
        return handler

    def do_logout(e):
        page.close(dlg)
        _logout(page)(e)

    items = [
        ft.ListTile(
            leading=ft.Icon(icon, color=theme.Colors.TEXT_MUTED),
            title=ft.Text(label, size=14, color=theme.Colors.TEXT),
            on_click=go_to(route),
        )
        for (label, route, icon, _sel) in secondary_items
    ]

    dlg = ft.AlertDialog(
        title=ft.Row(
            spacing=12,
            controls=[
                theme.brand_logo(size=36),
                ft.Column(
                    spacing=0,
                    controls=[
                        ft.Text(full_name, size=14, weight=ft.FontWeight.W_700,
                                color=theme.Colors.TEXT),
                        ft.Text(_sidebar_subtitle(page), size=10, weight=ft.FontWeight.W_600,
                                color=theme.Colors.TEXT_MUTED),
                    ],
                ),
            ],
        ),
        content=ft.Container(
            width=300,
            content=ft.Column(
                tight=True,
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    *items,
                    ft.Divider(height=1, color=theme.Colors.BORDER),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.LOGOUT, color=theme.Colors.ERROR),
                        title=ft.Text("Déconnexion", size=14, color=theme.Colors.ERROR),
                        on_click=do_logout,
                    ),
                ],
            ),
        ),
    )
    return dlg


def _mobile_appbar(page: ft.Page, title: str, actions: list | None = None,
                   drawer: ft.AlertDialog | None = None) -> ft.AppBar:
    profile = page.db.current_profile or {}
    full_name = profile.get("full_name", "A") or "A"

    def toggle_dark(e):
        theme.set_dark(page, not theme.is_dark(page))
        page.theme_mode = ft.ThemeMode.DARK if theme.is_dark() else ft.ThemeMode.LIGHT
        page.bgcolor = theme.Colors.BG
        _do_refresh(page)

    dark_btn = ft.IconButton(
        icon=ft.Icons.LIGHT_MODE_OUTLINED if theme.is_dark() else ft.Icons.DARK_MODE_OUTLINED,
        icon_size=20,
        icon_color=theme.Colors.TEXT_MUTED,
        on_click=toggle_dark,
    )
    notif_btn = ft.IconButton(
        icon=ft.Icons.NOTIFICATIONS_OUTLINED,
        icon_size=20,
        icon_color=theme.Colors.TEXT_MUTED,
        on_click=lambda e: page.open(_notifications_dialog(page)),
    )
    avatar = ft.Container(
        padding=ft.padding.only(right=12),
        content=ft.CircleAvatar(
            content=ft.Text(full_name[:1].upper(), size=13, weight=ft.FontWeight.BOLD),
            radius=16,
            bgcolor=theme.Colors.PRIMARY_ACTION,
            color=ft.Colors.WHITE,
        ),
    )
    # Bouton "menu" (☰) : n'apparaît que s'il y a des options secondaires à
    # ranger dans le tiroir (sinon tout tient déjà dans la barre du bas).
    leading = None
    if drawer is not None:
        leading = ft.IconButton(
            icon=ft.Icons.MENU,
            icon_color=theme.Colors.PRIMARY,
            on_click=lambda e: page.open(drawer),
        )
    return ft.AppBar(
        leading=leading,
        title=ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=theme.Colors.PRIMARY),
        bgcolor=theme.Colors.SURFACE,
        actions=[*(actions or []), notif_btn, dark_btn, avatar],
    )


# ---------------------------------------------------------------------------
# POINT D'ENTRÉE : construit la View complète d'une section principale
# ---------------------------------------------------------------------------
def shell_view(
    page: ft.Page,
    title: str,
    body: ft.Control,
    actions: list | None = None,
    floating_action_button: ft.FloatingActionButton | None = None,
) -> ft.View:
    """
    Construit une ft.View pour une section principale du rôle courant
    (étudiant, formateur ou administrateur), avec la navigation adaptée
    au rôle ET à la taille d'écran.
    """
    nav_items = get_nav_items(page)
    route = page.route
    active_index = next(
        (i for i, (_label, r, _icon, _sel) in enumerate(nav_items) if r == route), 0
    )

    # Historique pour le bouton retour de la topbar.
    history = _nav_state(page)["history"]
    if not history or history[-1] != route:
        history.append(route)

    if is_desktop(page):
        layout = ft.Row(
            expand=True,
            spacing=0,
            controls=[
                _sidebar(page, nav_items, active_index),
                ft.VerticalDivider(width=1, color=theme.Colors.BORDER),
                ft.Column(
                    expand=True,
                    spacing=0,
                    controls=[
                        _topbar(page, title, actions),
                        ft.Divider(height=1, color=theme.Colors.BORDER),
                        ft.Container(expand=True, content=body),
                    ],
                ),
            ],
        )
        return ft.View(
            route=route,
            bgcolor=theme.Colors.BG,
            padding=0,
            floating_action_button=floating_action_button,
            controls=[layout],
        )

    # Mobile : AppBar + contenu + barre de navigation en bas, réduite à
    # quelques destinations essentielles — le reste va dans le tiroir
    # latéral (☰) pour ne pas surcharger la barre.
    primary, secondary = split_mobile_nav(nav_items)
    primary_active_index = next(
        (i for i, (_l, r, _i, _s) in enumerate(primary) if r == route), None
    )
    drawer = _mobile_drawer(page, secondary) if secondary else None

    return ft.View(
        route=route,
        bgcolor=theme.Colors.BG,
        appbar=_mobile_appbar(page, title, actions, drawer=drawer),
        padding=0,
        floating_action_button=floating_action_button,
        controls=[ft.Container(expand=True, content=body)],
        navigation_bar=_bottom_nav(page, primary, primary_active_index),
    )
