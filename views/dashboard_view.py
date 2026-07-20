import flet as ft

from components import theme
from components.app_shell import shell_view


def build_dashboard_view(page: ft.Page) -> ft.View:
    """Onglet TABLEAU DE BORD : salutation, stats, reprise de cours, catalogue."""
    courses = page.db.get_courses()
    profile = page.db.current_profile or {}
    full_name = profile.get("full_name", "Apprenant") or "Apprenant"
    first_name = full_name.split(" ")[0]

    # Inscriptions + progression (une requête, réutilisée partout).
    enrollments = []
    try:
        enrollments = page.db.get_my_enrollments()
    except Exception:
        pass
    enrolled_ids = {en["course_id"] for en in enrollments}

    progress_by_course = {}
    for cid in enrolled_ids:
        try:
            progress_by_course[cid] = page.db.get_course_progress(cid)
        except Exception:
            progress_by_course[cid] = 0

    try:
        certificates = page.db.get_my_certificates()
    except Exception:
        certificates = []

    completed = sum(1 for p in progress_by_course.values() if p >= 100)

    # ------------------------------------------------------------------
    # RANGÉE DE STATISTIQUES (icônes pastel, façon dashboard pro)
    # ------------------------------------------------------------------
    stats = ft.ResponsiveRow(
        spacing=14,
        run_spacing=14,
        controls=[
            theme.stat_card(ft.Icons.AUTO_STORIES, "Cours disponibles", len(courses),
                            theme.Colors.PRIMARY_ACTION, col={"xs": 12, "sm": 6, "md": 3}),
            theme.stat_card(ft.Icons.PLAY_LESSON, "Mes inscriptions", len(enrollments),
                            theme.Colors.PURPLE, col={"xs": 12, "sm": 6, "md": 3}),
            theme.stat_card(ft.Icons.CHECK_CIRCLE, "Cours terminés", completed,
                            theme.Colors.SUCCESS, col={"xs": 12, "sm": 6, "md": 3}),
            theme.stat_card(ft.Icons.WORKSPACE_PREMIUM, "Brevets obtenus", len(certificates),
                            theme.Colors.CERT, col={"xs": 12, "sm": 6, "md": 3}),
        ],
    )

    # ------------------------------------------------------------------
    # CARTE HÉRO (dégradé bleu) : reprendre le cours en cours
    # ------------------------------------------------------------------
    hero = None
    in_progress = next(
        (en for en in enrollments
         if 0 <= progress_by_course.get(en["course_id"], 0) < 100),
        None,
    )
    if in_progress:
        c = in_progress.get("courses") or {}
        p = progress_by_course.get(in_progress["course_id"], 0)
        hero = ft.Container(
            padding=24,
            border_radius=20,
            gradient=theme.brand_gradient(),
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=12, vertical=5),
                        border_radius=theme.RADIUS_BADGE,
                        bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                        content=ft.Text("REPRENDRE L'APPRENTISSAGE", size=10,
                                        weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
                    ),
                    ft.Text(c.get("title", "Cours"), size=22, weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE),
                    ft.Text(c.get("category", "") or "Formation",
                            size=13, color=ft.Colors.with_opacity(0.85, ft.Colors.WHITE)),
                    ft.Container(height=4),
                    ft.Row(
                        spacing=16,
                        controls=[
                            ft.Container(
                                expand=True,
                                content=ft.Column(
                                    spacing=4,
                                    controls=[
                                        ft.ProgressBar(
                                            value=p / 100,
                                            color=ft.Colors.WHITE,
                                            bgcolor=ft.Colors.with_opacity(0.25, ft.Colors.WHITE),
                                            border_radius=6,
                                        ),
                                        ft.Text(f"{int(p)}% terminé", size=11,
                                                color=ft.Colors.with_opacity(0.85, ft.Colors.WHITE)),
                                    ],
                                ),
                            ),
                            theme.white_button(
                                "Continuer",
                                icon=ft.Icons.PLAY_ARROW_ROUNDED,
                                on_click=lambda e, cid=in_progress["course_id"]: page.go(f"/course/{cid}"),
                            ),
                        ],
                    ),
                ],
            ),
        )
    elif courses:
        # Pas de cours en cours : invitation à découvrir le catalogue.
        hero = ft.Container(
            padding=24,
            border_radius=20,
            gradient=theme.brand_gradient(),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Column(
                        expand=True,
                        spacing=6,
                        controls=[
                            ft.Text("Commencez votre apprentissage 🚀", size=20,
                                    weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ft.Text("Choisissez un cours dans le catalogue ci-dessous.",
                                    size=13, color=ft.Colors.with_opacity(0.85, ft.Colors.WHITE)),
                        ],
                    ),
                    ft.Icon(ft.Icons.SCHOOL_ROUNDED, size=56,
                            color=ft.Colors.with_opacity(0.35, ft.Colors.WHITE)),
                ],
            ),
        )

    # ------------------------------------------------------------------
    # CATALOGUE : recherche + filtre + grille de cartes
    # ------------------------------------------------------------------
    categories = sorted({(c.get("category") or "").strip() for c in courses if c.get("category")})

    def open_course(course_id):
        return lambda e: page.go(f"/course/{course_id}")

    def course_card(course):
        progress = progress_by_course.get(course["id"], 0) if course["id"] in enrolled_ids else 0
        is_enrolled = course["id"] in enrolled_ids

        shadow, border = theme.card_decor()
        return ft.Container(
            col={"xs": 12, "sm": 6, "md": 4},
            bgcolor=theme.Colors.SURFACE,
            border_radius=theme.RADIUS_CARD,
            shadow=shadow,
            border=border,
            on_click=open_course(course["id"]),
            ink=True,
            padding=0,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Column(
                spacing=0,
                controls=[
                    # Bandeau "couverture" en dégradé avec icône.
                    ft.Container(
                        height=96,
                        gradient=theme.brand_gradient(),
                        alignment=ft.alignment.center,
                        content=ft.Icon(ft.Icons.MENU_BOOK_ROUNDED, size=42,
                                        color=ft.Colors.with_opacity(0.9, ft.Colors.WHITE)),
                    ),
                    ft.Container(
                        padding=16,
                        content=ft.Column(
                            spacing=8,
                            controls=[
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls=[
                                        theme.category_badge(course.get("category", "") or "Général"),
                                        theme.chip("Inscrit ✓", theme.Colors.SUCCESS)
                                        if is_enrolled else ft.Container(),
                                    ],
                                ),
                                theme.subtitle(course["title"]),
                                ft.Text(
                                    course.get("description", "") or "",
                                    size=12,
                                    color=theme.Colors.TEXT_MUTED,
                                    max_lines=2,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                ft.Row(
                                    spacing=10,
                                    controls=[
                                        ft.Container(expand=True, content=theme.progress_bar(progress)),
                                        ft.Text(f"{int(progress)}%", size=11, weight=ft.FontWeight.BOLD,
                                                color=theme.Colors.SUCCESS if progress >= 100
                                                else theme.Colors.TEXT_MUTED),
                                    ],
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        )

    grid = ft.ResponsiveRow(spacing=16, run_spacing=16)
    empty_msg = theme.body("Aucun cours ne correspond à votre recherche.", muted=True)
    empty_msg.visible = False

    def compute_filtered():
        query = (search_field.value or "").strip().lower()
        selected_cat = category_dd.value or "Toutes"
        filtered = []
        for c in courses:
            title = (c.get("title") or "").lower()
            desc = (c.get("description") or "").lower()
            cat = (c.get("category") or "").strip()
            if query and query not in title and query not in desc:
                continue
            if selected_cat != "Toutes" and cat != selected_cat:
                continue
            filtered.append(c)
        return filtered

    def apply_filters(e=None):
        filtered = compute_filtered()
        grid.controls = [course_card(c) for c in filtered]
        empty_msg.visible = len(filtered) == 0
        page.update()

    search_field = ft.TextField(
        hint_text="Rechercher un cours…",
        prefix_icon=ft.Icons.SEARCH,
        border_radius=30,
        border_color=theme.Colors.BORDER,
        focused_border_color=theme.Colors.PRIMARY_ACTION,
        bgcolor=theme.Colors.SURFACE,
        content_padding=ft.padding.symmetric(horizontal=18, vertical=10),
        on_change=apply_filters,
        expand=True,
    )
    category_dd = ft.Dropdown(
        value="Toutes",
        width=170,
        border_radius=theme.RADIUS_INPUT,
        border_color=theme.Colors.BORDER,
        bgcolor=theme.Colors.SURFACE,
        options=[ft.dropdown.Option("Toutes")] + [ft.dropdown.Option(cat) for cat in categories],
        on_change=apply_filters,
    )

    # Recherche globale envoyée depuis la topbar : pré-remplit et filtre.
    global_q = getattr(page, "pending_search", "")
    page.pending_search = ""
    if global_q:
        search_field.value = global_q

    initial = compute_filtered()
    grid.controls = [course_card(c) for c in initial]
    empty_msg.visible = len(initial) == 0

    body_children = [
        theme.greeting("Bonjour, ", first_name),
        theme.body("Heureux de vous revoir. Continuez votre apprentissage !", muted=True),
        ft.Container(height=16),
        stats,
        ft.Container(height=16),
    ]
    if hero:
        body_children += [hero, ft.Container(height=20)]
    body_children += [
        ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[theme.section_title("Catalogue des cours")],
        ),
        ft.Container(height=4),
        ft.Row([search_field, category_dd], spacing=12),
        ft.Container(height=12),
        empty_msg,
        grid if courses else theme.body("Aucun cours disponible pour l'instant.", muted=True),
        ft.Container(height=20),
    ]

    body = ft.Container(
        padding=ft.padding.symmetric(horizontal=24, vertical=20),
        content=ft.Column(scroll=ft.ScrollMode.AUTO, controls=body_children),
    )

    return shell_view(page, title="Tableau de bord", body=body)
