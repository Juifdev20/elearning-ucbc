import flet as ft

from components import theme


def _field(label, value="", multiline=False, hint=""):
    return ft.TextField(
        label=label,
        value=value or "",
        hint_text=hint,
        multiline=multiline,
        min_lines=3 if multiline else 1,
        max_lines=6 if multiline else 1,
        border_radius=theme.RADIUS_INPUT,
        border_color=theme.Colors.BORDER,
        focused_border_color=theme.Colors.PRIMARY_ACTION,
    )


def _workflow_card(page: ft.Page, course_id: str, status: str, rejection_reason: str | None,
                   is_admin: bool) -> ft.Container:
    """Bloc du workflow d'approbation : statut courant + actions selon le rôle."""
    rows = [
        ft.Row(
            spacing=10,
            controls=[theme.subtitle("Statut de publication"), theme.course_status_chip(status)],
        ),
    ]

    if status == "rejected" and rejection_reason:
        rows.append(
            ft.Container(
                padding=12,
                border_radius=theme.RADIUS_INPUT,
                bgcolor=theme.tint(theme.Colors.ERROR, 0.10),
                content=ft.Row(
                    spacing=8,
                    controls=[
                        ft.Icon(ft.Icons.INFO_OUTLINE, size=18, color=theme.Colors.ERROR),
                        ft.Text(f"Motif du rejet : {rejection_reason}", size=12,
                                color=theme.Colors.ERROR, expand=True),
                    ],
                ),
            )
        )

    feedback = ft.Text("", size=12, color=theme.Colors.ERROR)

    def do_submit(e):
        try:
            page.db.submit_course_for_review(course_id)
            page.go(f"/admin/course/{course_id}")  # reconstruit avec le nouveau statut
        except Exception:
            feedback.value = "Erreur : écriture refusée. Avez-vous exécuté sql/course_approval.sql ?"
            page.update()

    def do_withdraw(e):
        try:
            page.db.withdraw_course(course_id)
            page.go(f"/admin/course/{course_id}")
        except Exception:
            feedback.value = "Erreur : écriture refusée. Avez-vous exécuté sql/course_approval.sql ?"
            page.update()

    if is_admin:
        # L'admin peut forcer n'importe quel statut directement.
        status_dd = ft.Dropdown(
            value=status,
            width=280,
            border_radius=theme.RADIUS_INPUT,
            border_color=theme.Colors.BORDER,
            options=[ft.dropdown.Option(key=k, text=v)
                    for k, v in theme.COURSE_STATUS_LABELS.items()],
        )
        reason_f = _field("Motif (si rejeté)", rejection_reason or "")

        def apply_status(e):
            try:
                page.db.update_course(course_id, {
                    "status": status_dd.value,
                    "rejection_reason": reason_f.value.strip() if status_dd.value == "rejected" else None,
                })
                page.go(f"/admin/course/{course_id}")
            except Exception:
                feedback.value = "Erreur : écriture refusée. Avez-vous exécuté sql/course_approval.sql ?"
                page.update()

        rows += [
            status_dd, reason_f, feedback,
            theme.primary_button("Mettre à jour le statut", icon=ft.Icons.SAVE_OUTLINED,
                                 width=240, on_click=apply_status),
        ]
    else:
        # Le formateur suit le workflow : soumettre, ou retirer un cours publié.
        if status in ("draft", "rejected"):
            rows.append(theme.body(
                "Ce cours n'est visible que par vous. Soumettez-le pour qu'un "
                "administrateur puisse le publier.", muted=True))
            rows.append(theme.primary_button(
                "Soumettre pour validation", icon=ft.Icons.SEND_OUTLINED,
                width=240, on_click=do_submit))
        elif status == "pending_review":
            rows.append(theme.body(
                "En attente de validation par un administrateur.", muted=True))
        elif status == "published":
            rows.append(theme.body(
                "Ce cours est publié et visible par tous les apprenants.", muted=True))
            rows.append(ft.OutlinedButton(
                "Retirer de la publication", icon=ft.Icons.UNPUBLISHED_OUTLINED,
                on_click=do_withdraw, style=ft.ButtonStyle(color=theme.Colors.ERROR)))
        rows.append(feedback)

    return theme.card(padding=20, content=ft.Column(spacing=12, controls=rows))


def build_course_editor_view(page: ft.Page, course_id: str | None) -> ft.View:
    """
    Éditeur de cours.
    - course_id is None  -> création d'un nouveau cours
    - course_id fourni   -> édition + gestion des leçons
    """
    editing = course_id is not None
    course = page.db.get_course(course_id) if editing else {}
    course = course or {}

    title_f = _field("Titre du cours", course.get("title", ""))
    desc_f = _field("Description", course.get("description", ""), multiline=True)
    cat_f = _field("Catégorie", course.get("category", ""), hint="Ex : Programmation")
    img_f = _field("URL de l'image de couverture", course.get("cover_image_url", ""),
                   hint="https://…")
    feedback = ft.Text("", size=13)
    status = course.get("status", "published" if course.get("is_published", True) else "draft")
    is_admin = page.db.is_admin()

    def save_course(e):
        feedback.value = ""
        if not title_f.value or not title_f.value.strip():
            feedback.value = "Le titre est obligatoire."
            feedback.color = theme.Colors.ERROR
            page.update()
            return
        fields = {
            "title": title_f.value.strip(),
            "description": desc_f.value.strip(),
            "category": cat_f.value.strip(),
            "cover_image_url": img_f.value.strip() or None,
        }
        try:
            if editing:
                page.db.update_course(course_id, fields)
                feedback.value = "Modifications enregistrées ✓"
                feedback.color = theme.Colors.SUCCESS
                page.update()
            else:
                created = page.db.create_course(**fields)
                if created:
                    page.go(f"/admin/course/{created['id']}")  # bascule en mode édition
                    return
                feedback.value = "Création impossible."
                feedback.color = theme.Colors.ERROR
                page.update()
        except Exception as ex:
            feedback.value = "Erreur : écriture refusée. Avez-vous exécuté sql/admin_policies.sql et un rôle formateur ?"
            feedback.color = theme.Colors.ERROR
            page.update()

    form_card = theme.card(
        padding=20,
        content=ft.Column(
            spacing=12,
            controls=[
                theme.section_title("Informations du cours"),
                title_f, desc_f, cat_f, img_f,
                feedback,
                theme.primary_button("Enregistrer", icon=ft.Icons.SAVE_OUTLINED, on_click=save_course),
            ],
        ),
    )

    controls = [
        theme.page_title("Nouveau cours" if not editing else "Éditer le cours"),
        ft.Container(height=10),
        form_card,
    ]

    if not editing:
        hint_text = theme.body(
            "Enregistrez d'abord ces infos : vous pourrez ensuite ajouter les leçons, "
            "avec leur lien vidéo (YouTube) et leur document PDF téléchargeable.",
            muted=True,
        )
        hint_text.expand = True
        controls.append(ft.Container(height=10))
        controls.append(
            ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=theme.Colors.TEXT_MUTED),
                    hint_text,
                ],
            )
        )

    # -------- Workflow d'approbation (uniquement en édition) --------
    if editing:
        controls.append(ft.Container(height=16))
        controls.append(_workflow_card(page, course_id, status, course.get("rejection_reason"), is_admin))

    # -------- Gestion des leçons (uniquement en édition) --------
    if editing:
        controls.append(ft.Container(height=20))
        controls.append(theme.section_title("Leçons"))
        lessons_col = ft.Column(spacing=10)

        def refresh_lessons():
            lessons = page.db.get_lessons(course_id)
            lessons_col.controls.clear()
            for i, lesson in enumerate(lessons):
                lessons_col.controls.append(_lesson_row(lesson, i, lessons))
            if not lessons:
                lessons_col.controls.append(theme.body("Aucune leçon. Ajoutez-en une ci-dessous.", muted=True))
            page.update()

        def edit_lesson_dialog(lesson):
            lt = _field("Titre", lesson.get("title", ""))
            lc = _field("Contenu", lesson.get("content", ""), multiline=True)
            lv = _field("Lien vidéo YouTube (optionnel)", lesson.get("video_url", ""), hint="https://youtube.com/watch?v=…")
            lf = _field("Document PDF du cours (optionnel)", lesson.get("file_url", ""), hint="https://…")

            def save(e):
                page.db.update_lesson(lesson["id"], {
                    "title": lt.value.strip(),
                    "content": lc.value.strip(),
                    "video_url": lv.value.strip() or None,
                    "file_url": lf.value.strip() or None,
                })
                page.close(dlg)
                refresh_lessons()

            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("Éditer la leçon"),
                content=ft.Container(width=320, height=420, content=ft.Column(
                    tight=True, spacing=10, scroll=ft.ScrollMode.AUTO,
                    controls=[lt, lc, lv, lf])),
                actions=[
                    ft.TextButton("Annuler", on_click=lambda e: page.close(dlg)),
                    ft.TextButton("Enregistrer", on_click=save,
                                  style=ft.ButtonStyle(color=theme.Colors.PRIMARY_ACTION)),
                ],
            )
            return lambda e: page.open(dlg)

        def move(lesson, others, delta):
            def handler(e):
                idx = others.index(lesson)
                j = idx + delta
                if 0 <= j < len(others):
                    page.db.swap_lesson_positions(lesson, others[j])
                    refresh_lessons()
            return handler

        def delete_lesson(lesson):
            def handler(e):
                page.db.delete_lesson(lesson["id"])
                refresh_lessons()
            return handler

        def _lesson_row(lesson, index, others):
            has_video = "🎬" if lesson.get("video_url") else ""
            has_pdf = "📄" if lesson.get("file_url") else ""
            return theme.card(
                padding=12,
                content=ft.Row(
                    controls=[
                        ft.Text(f"{index + 1}.", weight=ft.FontWeight.BOLD, color=theme.Colors.TEXT_MUTED),
                        ft.Text(f"{lesson.get('title', 'Leçon')} {has_video}{has_pdf}",
                                expand=True, color=theme.Colors.TEXT),
                        ft.IconButton(ft.Icons.ARROW_UPWARD, icon_size=18, tooltip="Monter",
                                      disabled=(index == 0), on_click=move(lesson, others, -1)),
                        ft.IconButton(ft.Icons.ARROW_DOWNWARD, icon_size=18, tooltip="Descendre",
                                      disabled=(index == len(others) - 1), on_click=move(lesson, others, +1)),
                        ft.IconButton(ft.Icons.EDIT_OUTLINED, icon_size=18, tooltip="Éditer",
                                      icon_color=theme.Colors.PRIMARY_ACTION, on_click=edit_lesson_dialog(lesson)),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=18, tooltip="Supprimer",
                                      icon_color=theme.Colors.ERROR, on_click=delete_lesson(lesson)),
                    ],
                ),
            )

        # Formulaire d'ajout de leçon.
        new_title = _field("Titre de la nouvelle leçon")
        new_content = _field("Contenu", multiline=True)
        new_video = _field("Lien vidéo YouTube (optionnel)", hint="https://youtube.com/watch?v=…")
        new_file = _field("Document PDF du cours (optionnel)", hint="https://…")
        add_feedback = ft.Text("", size=12, color=theme.Colors.ERROR)

        def add_lesson(e):
            if not new_title.value or not new_title.value.strip():
                add_feedback.value = "Le titre de la leçon est obligatoire."
                page.update()
                return
            try:
                page.db.create_lesson(
                    course_id,
                    title=new_title.value.strip(),
                    content=new_content.value.strip(),
                    video_url=new_video.value.strip() or None,
                    file_url=new_file.value.strip() or None,
                )
                new_title.value = new_content.value = new_video.value = new_file.value = ""
                add_feedback.value = ""
                refresh_lessons()
            except Exception:
                add_feedback.value = "Erreur : écriture refusée (policies RLS / rôle formateur ?)."
                page.update()

        add_card = theme.card(
            padding=16,
            content=ft.Column(
                spacing=10,
                controls=[
                    theme.subtitle("Ajouter une leçon"),
                    new_title, new_content, new_video, new_file, add_feedback,
                    theme.primary_button("Ajouter la leçon", icon=ft.Icons.ADD, width=220, on_click=add_lesson),
                ],
            ),
        )

        controls.append(lessons_col)
        controls.append(ft.Container(height=12))
        controls.append(add_card)
        refresh_lessons()

    back_route = "/admin/courses"
    return ft.View(
        route=f"/admin/course/{course_id}" if editing else "/admin/course/new",
        bgcolor=theme.Colors.BG,
        appbar=theme.branded_appbar(
            "Éditeur de cours",
            leading=ft.IconButton(ft.Icons.ARROW_BACK, icon_color=theme.Colors.PRIMARY,
                                  on_click=lambda e: page.go(back_route)),
        ),
        controls=[
            ft.Container(
                padding=20,
                expand=True,
                content=ft.Column(scroll=ft.ScrollMode.AUTO, controls=controls),
            )
        ],
    )
