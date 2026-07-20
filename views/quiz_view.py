import flet as ft

from services.certificate_service import generate_certificate, certificate_url
from components import theme


def build_quiz_view(page: ft.Page, course_id: str) -> ft.View:
    course = page.db.get_course(course_id)
    quiz = page.db.get_quiz(course_id)

    # Garde-fou anti-triche : impossible d'accéder au quiz (même par URL directe)
    # tant que toutes les leçons du cours n'ont pas été marquées terminées.
    lessons = page.db.get_lessons(course_id)
    progress = page.db.get_course_progress(course_id) if lessons else 100.0
    if lessons and progress < 100:
        return ft.View(
            route=f"/course/{course_id}/quiz",
            bgcolor=theme.Colors.BG,
            appbar=theme.branded_appbar(
                "Évaluation verrouillée",
                leading=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=theme.Colors.PRIMARY,
                    on_click=lambda e: page.go(f"/course/{course_id}"),
                ),
            ),
            controls=[
                ft.Container(
                    padding=20,
                    expand=True,
                    content=theme.card(
                        padding=24,
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
                            controls=[
                                theme.tinted_icon(ft.Icons.LOCK_OUTLINE, theme.Colors.CERT,
                                                  box=56, size=26),
                                theme.subtitle("Évaluation verrouillée"),
                                theme.body(
                                    f"Terminez toutes les leçons du cours ({round(progress)}% fait) "
                                    "avant de passer l'évaluation finale.",
                                    muted=True,
                                ),
                                ft.Container(height=6),
                                theme.primary_button(
                                    "Retour au cours",
                                    icon=ft.Icons.ARROW_BACK,
                                    width=220,
                                    on_click=lambda e: page.go(f"/course/{course_id}"),
                                ),
                            ],
                        ),
                    ),
                )
            ],
        )

    result_container = ft.Container(visible=False)
    question_controls = []  # liste de (question_id, radio_group, options)

    if not quiz:
        questions_column = ft.Column(
            controls=[theme.body("Aucun quiz n'est encore disponible pour ce cours.", muted=True)]
        )
    else:
        questions_column = ft.Column(spacing=20)
        questions = sorted(quiz.get("quiz_questions", []), key=lambda q: q.get("position", 0))

        for q in questions:
            radio_group = ft.RadioGroup(
                content=ft.Column(
                    controls=[
                        ft.Radio(
                            value=opt["id"],
                            label=opt["option_text"],
                            active_color=theme.Colors.PRIMARY_ACTION,
                        )
                        for opt in q.get("quiz_options", [])
                    ]
                )
            )
            question_controls.append((q["id"], radio_group, q.get("quiz_options", [])))
            questions_column.controls.append(
                theme.card(
                    content=ft.Column(
                        controls=[
                            ft.Text(q["question"], weight=ft.FontWeight.W_600, color=theme.Colors.TEXT),
                            radio_group,
                        ]
                    ),
                )
            )

    def submit_quiz(e):
        if not quiz:
            return
        total = len(question_controls)
        if total == 0:
            return

        # Retour visuel immédiat pendant la correction (requêtes réseau).
        submit_btn.text = "Correction en cours…"
        submit_btn.disabled = True
        page.update()

        correct = 0
        for question_id, radio_group, options in question_controls:
            selected_id = radio_group.value
            correct_option = next((o for o in options if o["is_correct"]), None)
            if selected_id and correct_option and selected_id == correct_option["id"]:
                correct += 1

        score = round((correct / total) * 100)
        pass_score = quiz.get("pass_score", 70)
        passed = score >= pass_score

        page.db.submit_quiz_attempt(quiz["id"], score, passed)

        result_container.visible = True
        result_container.content = _build_result(score, passed, pass_score)

        if passed:
            profile = page.db.current_profile or {}
            student_name = profile.get("full_name", "Apprenant")
            course_title = course["title"] if course else "Cours"
            generate_certificate(student_name=student_name, course_title=course_title, score=score,
                                avatar_url=profile.get("avatar_url"))
            page.db.create_certificate(course_id, certificate_url=certificate_url(student_name, course_title))

        submit_btn.text = "Soumettre mes réponses"
        submit_btn.disabled = False
        page.update()

    def _build_result(score, passed, pass_score):
        color = theme.Colors.SUCCESS if passed else theme.Colors.ERROR
        icon = ft.Icons.EMOJI_EVENTS if passed else ft.Icons.SENTIMENT_DISSATISFIED
        message = (
            "🎉 Félicitations ! Vous avez obtenu votre brevet."
            if passed
            else f"Score insuffisant (minimum requis : {pass_score}%). Révisez et retentez !"
        )
        return theme.card(
            padding=20,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(icon, size=48, color=color),
                    ft.Text(f"Votre score : {score}%", size=20, weight=ft.FontWeight.BOLD, color=theme.Colors.TEXT),
                    ft.Text(message, size=14, color=color, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=8),
                    theme.primary_button(
                        "Retour au cours",
                        icon=ft.Icons.ARROW_BACK,
                        width=240,
                        on_click=lambda e: page.go(f"/course/{course_id}"),
                    ),
                ],
            ),
        )

    submit_btn = theme.primary_button(
        "Soumettre mes réponses",
        icon=ft.Icons.SEND_ROUNDED,
        width=280,
        on_click=submit_quiz,
    )
    submit_btn.disabled = quiz is None

    return ft.View(
        route=f"/course/{course_id}/quiz",
        bgcolor=theme.Colors.BG,
        appbar=theme.branded_appbar(
            quiz["title"] if quiz else "Évaluation",
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                icon_color=theme.Colors.PRIMARY,
                on_click=lambda e: page.go(f"/course/{course_id}"),
            ),
        ),
        controls=[
            ft.Container(
                padding=20,
                expand=True,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        questions_column,
                        ft.Container(height=16),
                        ft.Row([submit_btn], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Container(height=16),
                        result_container,
                    ]
                ),
            )
        ],
    )
