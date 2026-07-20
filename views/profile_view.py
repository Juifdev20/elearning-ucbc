import os
from pathlib import Path

import flet as ft

from components import theme
from components.app_shell import shell_view
from services.supabase_service import forget_remembered_session

# Chemin ABSOLU (racine du projet, où vit main.py), pour correspondre EXACTEMENT
# à la résolution que fait Flet en interne pour upload_dir="uploads" passé à
# ft.app() — un chemin relatif ici dépendrait du répertoire de travail courant
# au lancement, qui peut différer selon comment l'app est démarrée.
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"


def build_profile_view(page: ft.Page) -> ft.View:
    """Onglet PROFIL : identité modifiable (nom, photo, mot de passe — tous
    rôles), statistiques et raccourcis vers les pages dédiées (étudiant)."""
    profile = page.db.current_profile or {}
    is_student = (profile.get("role", "student") or "student") == "student"

    enrollments, certificates = [], []
    if is_student:
        try:
            enrollments = page.db.get_my_enrollments()
        except Exception:
            enrollments = []
        try:
            certificates = page.db.get_my_certificates()
        except Exception:
            certificates = []

    def logout(e):
        page.db.sign_out()
        forget_remembered_session(page)
        page.go("/login")

    full_name = profile.get("full_name", "") or "Apprenant"
    role = (profile.get("role", "student") or "student").capitalize()
    email = getattr(page.db.current_user, "email", "") or ""
    avatar_url = profile.get("avatar_url")

    # ------------------------------------------------------------------
    # EN-TÊTE : bannière dégradée + avatar (modifiable) + identité
    # ------------------------------------------------------------------
    avatar_display = ft.CircleAvatar(
        foreground_image_src=avatar_url,
        content=ft.Text(full_name[:1].upper(), size=26, weight=ft.FontWeight.BOLD),
        radius=34,
        bgcolor=ft.Colors.WHITE,
        color=theme.Colors.PRIMARY,
    )
    avatar_feedback = ft.Text("", size=11, color=ft.Colors.WHITE)

    def on_avatar_uploaded(e: ft.FilePickerUploadEvent):
        if e.error:
            avatar_feedback.value = f"Échec de l'envoi ({e.error})."
            page.update()
            return
        # IMPORTANT : ne JAMAIS comparer une progression flottante avec ==1 —
        # le navigateur peut rapporter 0.999999... (arrondi), une égalité
        # stricte ne se déclenche alors jamais et l'UI reste bloquée sur
        # "Envoi en cours" indéfiniment (bug constaté : c'était exactement ça).
        if e.progress is not None and e.progress < 0.999:
            avatar_feedback.value = f"Envoi en cours… {int(e.progress * 100)}%"
            page.update()
            return

        local_path = str(UPLOAD_DIR / e.file_name)
        try:
            ext = e.file_name.rsplit(".", 1)[-1] if "." in e.file_name else "jpg"
            new_url = page.db.upload_avatar(local_path, ext)
            avatar_display.foreground_image_src = new_url
            avatar_feedback.value = "Photo mise à jour ✓"
        except FileNotFoundError:
            avatar_feedback.value = "Échec : fichier introuvable après l'envoi."
        except Exception:
            avatar_feedback.value = "Échec (bucket 'avatars' créé ? sql/avatars_storage.sql)"
        finally:
            try:
                os.remove(local_path)
            except OSError:
                pass
            page.update()

    def on_avatar_picked(e: ft.FilePickerResultEvent):
        if not e.files:
            return
        f = e.files[0]
        avatar_feedback.value = "Envoi en cours…"
        page.update()
        upload_url = page.get_upload_url(f.name, 600)
        avatar_picker.upload([ft.FilePickerUploadFile(f.name, upload_url=upload_url)])

    avatar_picker = ft.FilePicker(on_result=on_avatar_picked, on_upload=on_avatar_uploaded)
    page.overlay.append(avatar_picker)

    change_photo_btn = ft.TextButton(
        "Changer la photo",
        icon=ft.Icons.CAMERA_ALT_OUTLINED,
        on_click=lambda e: avatar_picker.pick_files(
            allow_multiple=False,
            file_type=ft.FilePickerFileType.IMAGE,
        ),
        style=ft.ButtonStyle(color=ft.Colors.WHITE),
    )

    header = ft.Container(
        border_radius=20,
        gradient=theme.brand_gradient(),
        padding=24,
        content=ft.Row(
            spacing=18,
            controls=[
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                    controls=[avatar_display, change_photo_btn, avatar_feedback],
                ),
                ft.Column(
                    expand=True,
                    spacing=4,
                    controls=[
                        ft.Text(full_name, size=20, weight=ft.FontWeight.BOLD,
                                color=ft.Colors.WHITE,
                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(email, size=12, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                                color=ft.Colors.with_opacity(0.85, ft.Colors.WHITE)),
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=12, vertical=4),
                            border_radius=theme.RADIUS_BADGE,
                            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                            content=ft.Text(role, size=11, weight=ft.FontWeight.W_700,
                                            color=ft.Colors.WHITE),
                        ),
                    ],
                ),
            ],
        ),
    )

    # ------------------------------------------------------------------
    # MODIFIER LE PROFIL : nom + mot de passe — disponible pour TOUS les
    # rôles (étudiant, formateur, admin), pas seulement l'étudiant.
    # ------------------------------------------------------------------
    name_field = theme.text_field("Nom complet", icon=ft.Icons.PERSON_OUTLINE)
    name_field.value = full_name
    name_feedback = ft.Text("", size=12)

    def save_name(e):
        new_name = (name_field.value or "").strip()
        if not new_name:
            name_feedback.value = "Le nom ne peut pas être vide."
            name_feedback.color = theme.Colors.ERROR
            page.update()
            return
        try:
            page.db.update_profile({"full_name": new_name})
            name_feedback.value = "Nom mis à jour ✓"
            name_feedback.color = theme.Colors.SUCCESS
        except Exception:
            name_feedback.value = "Erreur : écriture refusée."
            name_feedback.color = theme.Colors.ERROR
        page.update()

    identity_card = theme.card(
        padding=20,
        content=ft.Column(
            spacing=10,
            controls=[
                theme.subtitle("Nom affiché"),
                name_field,
                name_feedback,
                theme.primary_button("Enregistrer le nom", icon=ft.Icons.SAVE_OUTLINED,
                                     width=220, on_click=save_name),
            ],
        ),
    )

    new_pw_field = theme.text_field("Nouveau mot de passe", password=True, icon=ft.Icons.LOCK_OUTLINE)
    confirm_pw_field = theme.text_field("Confirmer le mot de passe", password=True, icon=ft.Icons.LOCK_OUTLINE)
    pw_feedback = ft.Text("", size=12)

    def save_password(e):
        pw = new_pw_field.value or ""
        if len(pw) < 6:
            pw_feedback.value = "Le mot de passe doit contenir au moins 6 caractères."
            pw_feedback.color = theme.Colors.ERROR
            page.update()
            return
        if pw != (confirm_pw_field.value or ""):
            pw_feedback.value = "Les deux mots de passe ne correspondent pas."
            pw_feedback.color = theme.Colors.ERROR
            page.update()
            return
        try:
            page.db.update_password(pw)
            new_pw_field.value = ""
            confirm_pw_field.value = ""
            pw_feedback.value = "Mot de passe changé ✓"
            pw_feedback.color = theme.Colors.SUCCESS
        except Exception:
            pw_feedback.value = "Erreur lors du changement de mot de passe."
            pw_feedback.color = theme.Colors.ERROR
        page.update()

    password_card = theme.card(
        padding=20,
        content=ft.Column(
            spacing=10,
            controls=[
                theme.subtitle("Changer le mot de passe"),
                new_pw_field,
                confirm_pw_field,
                pw_feedback,
                theme.primary_button("Changer le mot de passe", icon=ft.Icons.LOCK_RESET,
                                     width=240, on_click=save_password),
            ],
        ),
    )

    completed = sum(
        1 for en in enrollments
        if page.db.get_course_progress((en.get("courses") or {}).get("id", "")) >= 100
    ) if is_student else 0

    body_controls = [
        header,
        ft.Container(height=16),
        identity_card,
        ft.Container(height=12),
        password_card,
        ft.Container(height=16),
    ]

    if is_student:
        # Statistiques rapides + raccourcis vers les pages dédiées (pas de
        # duplication du détail, déjà présent dans Progression/Certificats).
        stats = ft.ResponsiveRow(
            spacing=14,
            run_spacing=14,
            controls=[
                theme.stat_card(ft.Icons.MENU_BOOK, "Cours suivis", len(enrollments),
                                theme.Colors.PRIMARY_ACTION, col={"xs": 12, "sm": 4}),
                theme.stat_card(ft.Icons.CHECK_CIRCLE, "Terminés", completed,
                                theme.Colors.SUCCESS, col={"xs": 12, "sm": 4}),
                theme.stat_card(ft.Icons.WORKSPACE_PREMIUM, "Brevets", len(certificates),
                                theme.Colors.CERT, col={"xs": 12, "sm": 4}),
            ],
        )

        def shortcut_row(icon, color, label, sub, route):
            return theme.card(
                padding=14,
                on_click=lambda e: page.go(route),
                ink=True,
                content=ft.Row(
                    spacing=12,
                    controls=[
                        theme.tinted_icon(icon, color, box=40, size=20),
                        ft.Column(
                            expand=True, spacing=2,
                            controls=[
                                ft.Text(label, weight=ft.FontWeight.W_600, size=13,
                                        color=theme.Colors.TEXT),
                                ft.Text(sub, size=11, color=theme.Colors.TEXT_MUTED),
                            ],
                        ),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, color=theme.Colors.TEXT_MUTED),
                    ],
                ),
            )

        body_controls += [
            stats,
            ft.Container(height=20),
            shortcut_row(ft.Icons.TRENDING_UP, theme.Colors.PRIMARY_ACTION,
                        "Voir ma progression détaillée", "Par cours + historique d'activité",
                        "/progress"),
            ft.Container(height=10),
            shortcut_row(ft.Icons.WORKSPACE_PREMIUM, theme.Colors.CERT,
                        "Voir mes certificats", f"{len(certificates)} brevet(s) obtenu(s)",
                        "/certificates"),
            ft.Container(height=10),
            shortcut_row(ft.Icons.LEADERBOARD, theme.Colors.PURPLE,
                        "Voir le classement", "Comparez-vous aux autres apprenants",
                        "/leaderboard"),
            ft.Container(height=24),
        ]

    body_controls += [
        ft.OutlinedButton(
            "Se déconnecter",
            icon=ft.Icons.LOGOUT,
            on_click=logout,
            style=ft.ButtonStyle(color=theme.Colors.ERROR),
        ),
        ft.Container(height=20),
    ]

    body = ft.Container(
        padding=ft.padding.symmetric(horizontal=24, vertical=20),
        content=ft.Column(scroll=ft.ScrollMode.AUTO, controls=body_controls),
    )

    return shell_view(page, title="Mon profil", body=body)
