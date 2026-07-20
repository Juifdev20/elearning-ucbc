import flet as ft

from components import theme
from components.app_shell import shell_view


def build_admin_dashboard_view(page: ft.Page) -> ft.View:
    """Page COURS : liste et gestion des cours (formateur : les siens ; admin : tous)."""
    is_admin = page.db.is_admin()
    try:
        courses = page.db.get_all_courses(mine_only=not is_admin)
    except Exception:
        courses = []

    def _count(s):
        return sum(1 for c in courses
                   if c.get("status", "published" if c.get("is_published", True) else "draft") == s)

    stats = ft.ResponsiveRow(
        spacing=14,
        run_spacing=14,
        controls=[
            theme.stat_card(ft.Icons.AUTO_STORIES, "Total", len(courses),
                            theme.Colors.PRIMARY_ACTION, col={"xs": 12, "sm": 6, "md": 3}),
            theme.stat_card(ft.Icons.PUBLIC, "Publiés", _count("published"),
                            theme.Colors.SUCCESS, col={"xs": 12, "sm": 6, "md": 3}),
            theme.stat_card(ft.Icons.PENDING_ACTIONS, "En attente", _count("pending_review"),
                            theme.Colors.CERT, col={"xs": 12, "sm": 6, "md": 3}),
            theme.stat_card(ft.Icons.EDIT_NOTE, "Brouillons/Rejetés",
                            _count("draft") + _count("rejected"),
                            theme.Colors.TEXT_MUTED, col={"xs": 12, "sm": 6, "md": 3}),
        ],
    )

    def confirm_delete(course_id, title):
        def do_delete(e):
            try:
                page.db.delete_course(course_id)
            except Exception:
                pass
            page.close(dlg)
            page.go("/admin/courses")  # reconstruit la liste

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Supprimer le cours ?"),
            content=ft.Text(f"« {title} » et tout son contenu seront définitivement supprimés."),
            actions=[
                ft.TextButton("Annuler", on_click=lambda e: page.close(dlg)),
                ft.TextButton("Supprimer", on_click=do_delete,
                              style=ft.ButtonStyle(color=theme.Colors.ERROR)),
            ],
        )
        return lambda e: page.open(dlg)

    def action_btn(label, icon, color, on_click):
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=12, vertical=7),
            border_radius=8,
            bgcolor=theme.tint(color, 0.10),
            ink=True,
            on_click=on_click,
            content=ft.Row(
                spacing=6,
                tight=True,
                controls=[
                    ft.Icon(icon, size=15, color=color),
                    ft.Text(label, size=12, weight=ft.FontWeight.W_600, color=color),
                ],
            ),
        )

    def course_row(course):
        cid = course["id"]
        status = course.get("status", "published" if course.get("is_published", True) else "draft")
        return theme.card(
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Row(
                        spacing=14,
                        controls=[
                            theme.tinted_icon(ft.Icons.MENU_BOOK_ROUNDED,
                                              theme.Colors.PRIMARY_ACTION, box=48, size=22),
                            ft.Column(
                                expand=True,
                                spacing=3,
                                controls=[
                                    theme.subtitle(course.get("title", "Cours")),
                                    ft.Row(
                                        spacing=8,
                                        controls=[
                                            theme.chip(course.get("category", "") or "Sans catégorie",
                                                       theme.Colors.PURPLE),
                                            theme.course_status_chip(status),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.Row(
                        wrap=True,
                        spacing=8,
                        run_spacing=8,
                        controls=[
                            action_btn("Éditer", ft.Icons.EDIT_OUTLINED, theme.Colors.PRIMARY_ACTION,
                                       lambda e, c=cid: page.go(f"/admin/course/{c}")),
                            action_btn("Quiz", ft.Icons.QUIZ_OUTLINED, theme.Colors.PURPLE,
                                       lambda e, c=cid: page.go(f"/admin/course/{c}/quiz")),
                            action_btn("Apprenants", ft.Icons.GROUP_OUTLINED, theme.Colors.TEAL,
                                       lambda e, c=cid: page.go(f"/admin/course/{c}/learners")),
                            action_btn("Supprimer", ft.Icons.DELETE_OUTLINE, theme.Colors.ERROR,
                                       confirm_delete(cid, course.get("title", "Cours"))),
                        ],
                    ),
                ],
            ),
        )

    # Recherche : préremplie si l'utilisateur a tapé une requête dans la
    # barre globale de la topbar (voir components/app_shell.py).
    global_q = getattr(page, "pending_search", "")
    page.pending_search = ""

    rows_col = ft.Column(spacing=12)
    empty_msg = theme.body("Aucun cours ne correspond à votre recherche.", muted=True)
    empty_msg.visible = False

    def render(filtered):
        if filtered:
            rows_col.controls = [course_row(c) for c in filtered]
            empty_msg.visible = False
        elif courses:
            rows_col.controls = []
            empty_msg.visible = True
        else:
            rows_col.controls = [
                theme.card(
                    padding=32,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                        controls=[
                            theme.tinted_icon(ft.Icons.ADD_BOX_OUTLINED, theme.Colors.PRIMARY_ACTION,
                                              box=64, size=32, radius=18),
                            theme.subtitle("Aucun cours pour l'instant"),
                            theme.body("Créez votre premier cours avec le bouton ci-dessous.",
                                       muted=True),
                        ],
                    ),
                )
            ]
            empty_msg.visible = False

    def apply_search(e=None):
        q = (search_field.value or "").strip().lower()
        filtered = [c for c in courses if q in (c.get("title", "") or "").lower()
                   or q in (c.get("category", "") or "").lower()] if q else courses
        render(filtered)
        page.update()

    search_field = ft.TextField(
        hint_text="Rechercher un cours…",
        value=global_q,
        prefix_icon=ft.Icons.SEARCH,
        border_radius=30,
        border_color=theme.Colors.BORDER,
        focused_border_color=theme.Colors.PRIMARY_ACTION,
        bgcolor=theme.Colors.SURFACE,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=8),
        on_change=apply_search,
    )

    initial = [c for c in courses if global_q.lower() in (c.get("title", "") or "").lower()
              or global_q.lower() in (c.get("category", "") or "").lower()] if global_q else courses
    render(initial)

    body = ft.Container(
        padding=ft.padding.symmetric(horizontal=24, vertical=20),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                theme.page_title("Gestion des cours"),
                theme.body(
                    "Créez et gérez vos cours, leçons, quiz et apprenants." if is_admin
                    else "Créez et gérez les cours dont vous êtes formateur.", muted=True),
                ft.Container(height=16),
                stats,
                ft.Container(height=20),
                theme.section_title("Vos cours"),
                ft.Container(height=8),
                search_field,
                ft.Container(height=12),
                empty_msg,
                rows_col,
                ft.Container(height=70),  # espace pour le FAB
            ],
        ),
    )

    return shell_view(
        page,
        title="Cours",
        body=body,
        floating_action_button=ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            text="Nouveau cours",
            bgcolor=theme.Colors.PRIMARY_ACTION,
            foreground_color=ft.Colors.WHITE,
            on_click=lambda e: page.go("/admin/course/new"),
        ),
    )
