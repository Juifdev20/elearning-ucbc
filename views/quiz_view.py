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
    question_controls = []  # liste de (question_id, radio_group, options, card_ref)

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
            status_icon = ft.Icon(visible=False, size=20)
            card = theme.card(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(q["question"], weight=ft.FontWeight.W_600,
                                        color=theme.Colors.TEXT, expand=True),
                                status_icon,
                            ],
                        ),
                        radio_group,
                    ]
                ),
            )
            question_controls.append((q["id"], radio_group, q.get("quiz_options", []), card, status_icon))
            questions_column.controls.append(card)

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
        # Corrige chaque question : verrouille le choix de l'étudiant et
        # marque la carte en vert/rouge SANS jamais révéler la bonne
        # réponse — seulement s'il avait juste ou faux.
        for question_id, radio_group, options, card, status_icon in question_controls:
            selected_id = radio_group.value
            correct_option = next((o for o in options if o["is_correct"]), None)
            is_correct = bool(selected_id and correct_option and selected_id == correct_option["id"])
            if is_correct:
                correct += 1
            radio_group.disabled = True
            status_icon.name = ft.Icons.CHECK_CIRCLE if is_correct else ft.Icons.CANCEL
            status_icon.color = theme.Colors.SUCCESS if is_correct else theme.Colors.ERROR
            status_icon.visible = True
            card.border = ft.border.all(2, theme.Colors.SUCCESS if is_correct else theme.Colors.ERROR)

        score = round((correct / total) * 100)
        pass_score = quiz.get("pass_score", 70)
        passed = score >= pass_score

        page.db.submit_quiz_attempt(quiz["id"], score, passed)

        if passed:
            profile = page.db.current_profile or {}
            student_name = profile.get("full_name", "Apprenant")
            course_title = course["title"] if course else "Cours"
            generate_certificate(student_name=student_name, course_title=course_title, score=score,
                                avatar_url=profile.get("avatar_url"))
            page.db.create_certificate(course_id, certificate_url=certificate_url(student_name, course_title))
            must_retake_course = False
        else:
            # 1er échec : retenter directement l'évaluation est permis.
            # 2e échec CONSÉCUTIF : l'apprenant doit reprendre tout le cours
            # (sa progression sur les leçons est effacée, ce qui reverrouille
            # l'évaluation via le garde-fou déjà en place plus haut).
            try:
                consecutive_fails = page.db.count_consecutive_failed_attempts(quiz["id"])
            except Exception:
                consecutive_fails = 1
            must_retake_course = consecutive_fails >= 2
            if must_retake_course:
                try:
                    page.db.reset_course_progress(course_id)
                except Exception:
                    pass

        result_container.visible = True
        result_container.content = _build_result(score, passed, pass_score, must_retake_course)

        # La suite se joue via les boutons du bloc résultat (Retenter /
        # Retour au cours) — le bouton de soumission n'a plus lieu d'être.
        submit_btn.visible = False
        page.update()

    def _retry_quiz(e):
        # Reconstruit entièrement la page (nouvelle tentative, réponses
        # effacées) : un simple page.go() vers la même route redéclenche
        # la construction de la vue depuis zéro.
        page.go(f"/course/{course_id}/quiz")

    def _build_result(score, passed, pass_score, must_retake_course):
        color = theme.Colors.SUCCESS if passed else theme.Colors.ERROR
        icon = ft.Icons.EMOJI_EVENTS if passed else ft.Icons.SENTIMENT_DISSATISFIED
        if passed:
            message = "🎉 Félicitations ! Vous avez obtenu votre brevet."
        elif must_retake_course:
            message = (
                f"Score insuffisant (minimum requis : {pass_score}%), 2 échecs consécutifs. "
                "Vous devez reprendre le cours (toutes les leçons) avant de retenter l'évaluation."
            )
        else:
            message = f"Score insuffisant (minimum requis : {pass_score}%). Vous pouvez retenter tout de suite."

        actions = [
            theme.primary_button(
                "Retour au cours",
                icon=ft.Icons.ARROW_BACK,
                width=240,
                on_click=lambda e: page.go(f"/course/{course_id}"),
            ),
        ]
        if not passed and not must_retake_course:
            actions.insert(0, theme.primary_button(
                "Retenter l'évaluation",
                icon=ft.Icons.REPLAY,
                width=240,
                on_click=_retry_quiz,
            ))

        return theme.card(
            padding=20,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(icon, size=48, color=color),
                    ft.Text(f"Votre score : {score}%", size=20, weight=ft.FontWeight.BOLD, color=theme.Colors.TEXT),
                    ft.Text(message, size=14, color=color, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=8),
                    ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10, controls=actions),
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
