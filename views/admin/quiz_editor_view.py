import flet as ft

from services.supabase_service import db
from components import theme


def _field(label, value="", multiline=False, width=None):
    return ft.TextField(
        label=label,
        value=value or "",
        multiline=multiline,
        width=width,
        border_radius=theme.RADIUS_INPUT,
        border_color=theme.Colors.BORDER,
        focused_border_color=theme.Colors.PRIMARY_ACTION,
    )


def build_quiz_editor_view(page: ft.Page, course_id: str) -> ft.View:
    """Éditeur du quiz final d'un cours : seuil, questions, options, bonne réponse."""
    course = db.get_course(course_id)
    quiz = db.get_or_create_quiz(course_id)
    quiz_id = quiz["id"] if quiz else None

    def load_questions():
        if not quiz_id:
            return []
        res = (
            db.client.table("quiz_questions")
            .select("*, quiz_options(*)")
            .eq("quiz_id", quiz_id)
            .order("position")
            .execute()
        )
        return res.data or []

    # --- Seuil de réussite ---
    pass_f = _field("Seuil de réussite (%)", str(quiz.get("pass_score", 70)) if quiz else "70", width=200)
    pass_feedback = ft.Text("", size=12)

    def save_pass(e):
        try:
            val = int(pass_f.value)
            val = max(0, min(100, val))
            db.update_quiz(quiz_id, {"pass_score": val})
            pass_f.value = str(val)
            pass_feedback.value = "Seuil enregistré ✓"
            pass_feedback.color = theme.Colors.SUCCESS
        except ValueError:
            pass_feedback.value = "Entrez un nombre entre 0 et 100."
            pass_feedback.color = theme.Colors.ERROR
        except Exception:
            pass_feedback.value = "Écriture refusée (policies RLS / rôle formateur ?)."
            pass_feedback.color = theme.Colors.ERROR
        page.update()

    # --- Liste des questions existantes ---
    questions_col = ft.Column(spacing=10)

    def refresh_questions():
        questions = load_questions()
        questions_col.controls.clear()
        for i, q in enumerate(questions):
            questions_col.controls.append(_question_row(q, i))
        if not questions:
            questions_col.controls.append(theme.body("Aucune question. Ajoutez-en une ci-dessous.", muted=True))
        page.update()

    def delete_question(qid):
        def handler(e):
            db.delete_question(qid)  # options supprimées en cascade (FK on delete cascade)
            refresh_questions()
        return handler

    def _question_row(q, index):
        options = q.get("quiz_options", [])
        option_lines = [
            ft.Row(
                spacing=6,
                controls=[
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE if opt.get("is_correct") else ft.Icons.RADIO_BUTTON_UNCHECKED,
                        size=16,
                        color=theme.Colors.SUCCESS if opt.get("is_correct") else theme.Colors.TEXT_MUTED,
                    ),
                    ft.Text(opt.get("option_text", ""), size=13, color=theme.Colors.TEXT),
                ],
            )
            for opt in options
        ]
        return theme.card(
            content=ft.Column(
                spacing=6,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(f"{index + 1}. {q.get('question', '')}",
                                    weight=ft.FontWeight.W_600, expand=True, color=theme.Colors.TEXT),
                            ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=18, tooltip="Supprimer",
                                          icon_color=theme.Colors.ERROR, on_click=delete_question(q["id"])),
                        ],
                    ),
                    *option_lines,
                ],
            ),
        )

    # --- Formulaire d'ajout de question ---
    q_text = _field("Énoncé de la question")
    opt_fields = [_field(f"Option {i + 1}") for i in range(4)]
    correct_group = ft.RadioGroup(
        value="0",
        content=ft.Row(
            controls=[ft.Radio(value=str(i), label=f"Bonne réponse : {i + 1}",
                               active_color=theme.Colors.SUCCESS) for i in range(4)],
            wrap=True,
        ),
    )
    add_feedback = ft.Text("", size=12, color=theme.Colors.ERROR)

    def add_question(e):
        add_feedback.value = ""
        if not q_text.value or not q_text.value.strip():
            add_feedback.value = "L'énoncé est obligatoire."
            page.update()
            return
        filled = [(i, f.value.strip()) for i, f in enumerate(opt_fields) if f.value and f.value.strip()]
        if len(filled) < 2:
            add_feedback.value = "Fournissez au moins 2 options."
            page.update()
            return
        correct_index = int(correct_group.value)
        if correct_index not in [i for i, _ in filled]:
            add_feedback.value = "La bonne réponse doit correspondre à une option remplie."
            page.update()
            return
        try:
            question = db.create_question(quiz_id, q_text.value.strip())
            for i, text in filled:
                db.create_option(question["id"], text, is_correct=(i == correct_index))
            # Réinitialise le formulaire.
            q_text.value = ""
            for f in opt_fields:
                f.value = ""
            correct_group.value = "0"
            refresh_questions()
        except Exception:
            add_feedback.value = "Écriture refusée (policies RLS / rôle formateur ?)."
            page.update()

    add_card = theme.card(
        padding=16,
        content=ft.Column(
            spacing=10,
            controls=[
                theme.subtitle("Ajouter une question"),
                q_text,
                *opt_fields,
                correct_group,
                add_feedback,
                theme.primary_button("Ajouter la question", icon=ft.Icons.ADD, width=240, on_click=add_question),
            ],
        ),
    )

    pass_card = theme.card(
        padding=16,
        content=ft.Column(
            spacing=10,
            controls=[
                theme.subtitle("Seuil de réussite"),
                ft.Row([pass_f, theme.primary_button("Enregistrer", width=160, on_click=save_pass)],
                       spacing=12, vertical_alignment=ft.CrossAxisAlignment.START),
                pass_feedback,
            ],
        ),
    )

    refresh_questions()

    return ft.View(
        route=f"/admin/course/{course_id}/quiz",
        bgcolor=theme.Colors.BG,
        appbar=theme.branded_appbar(
            f"Quiz — {course['title'] if course else 'Cours'}",
            leading=ft.IconButton(ft.Icons.ARROW_BACK, icon_color=theme.Colors.PRIMARY,
                                  on_click=lambda e: page.go(f"/admin/course/{course_id}")),
        ),
        controls=[
            ft.Container(
                padding=20,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        theme.page_title("Éditeur de quiz"),
                        ft.Container(height=10),
                        pass_card,
                        ft.Container(height=16),
                        theme.section_title("Questions"),
                        questions_col,
                        ft.Container(height=12),
                        add_card,
                    ],
                ),
            )
        ],
    )
