"""
Génère un certificat PDF professionnel quand un apprenant réussit
le quiz final d'un cours.
"""
import os
import re
from io import BytesIO
from pathlib import Path
from datetime import date

import httpx
from PIL import Image
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.colors import HexColor
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Les PDF sont écrits DANS le dossier assets/ (et non un dossier à part) pour
# que Flet les serve automatiquement en HTTP, à la même adresse en local et
# une fois déployé (un chemin absolu type file:///C:/... ou un lien "assets
# locaux" ne fonctionne QUE si le navigateur tourne sur la même machine que
# le serveur — ça casse dès que l'app est hébergée ailleurs, ex. Render).
BASE_DIR = Path(__file__).resolve().parent.parent
CERT_DIR = BASE_DIR / "assets" / "certificates"
LOGO_PATH = BASE_DIR / "assets" / "icons" / "icon-512.png"

# Police manuscrite pour le titre "Certificat" — Great Vibes (Google Fonts,
# licence SIL Open Font, libre de redistribution) : embarquée dans le projet
# pour un rendu identique en local ET une fois déployé (ne dépend PAS des
# polices installées sur la machine, contrairement à une police système).
SCRIPT_FONT_PATH = BASE_DIR / "assets" / "fonts" / "GreatVibes-Regular.ttf"
SCRIPT_FONT = "Helvetica-Oblique"  # repli si la police ne se charge pas
try:
    pdfmetrics.registerFont(TTFont("GreatVibes", str(SCRIPT_FONT_PATH)))
    SCRIPT_FONT = "GreatVibes"
except Exception:
    pass

NAVY = HexColor("#1E3A8A")
BLUE = HexColor("#2563EB")
BLUE_PALE = HexColor("#DBEAFE")
GOLD = HexColor("#F59E0B")
GOLD_DARK = HexColor("#B45309")
INK = HexColor("#111827")
GRAY = HexColor("#4B5563")


def _safe(text: str) -> str:
    """Nettoie un texte pour en faire un nom de fichier sûr."""
    return re.sub(r"[^A-Za-z0-9_-]", "", text.replace(" ", "_"))


def _filename(student_name: str, course_title: str) -> str:
    return f"certificat_{_safe(student_name)}_{_safe(course_title)}.pdf"


def certificate_path(student_name: str, course_title: str) -> str:
    """Chemin absolu (disque) déterministe du PDF pour un (apprenant, cours) donné."""
    return str(CERT_DIR / _filename(student_name, course_title))


def certificate_url(student_name: str, course_title: str) -> str:
    """Chemin URL (servi par Flet) du PDF — utilisable directement dans
    `page.launch_url()`, en local comme en production."""
    return f"/certificates/{_filename(student_name, course_title)}"


def ensure_certificate(student_name: str, course_title: str, score: int, avatar_url: str = None) -> str:
    """Génère le certificat s'il n'existe pas encore, retourne son URL de téléchargement."""
    path = certificate_path(student_name, course_title)
    if not os.path.exists(path):
        generate_certificate(student_name, course_title, score, avatar_url=avatar_url)
    return certificate_url(student_name, course_title)


def _fetch_avatar(avatar_url: str):
    """Télécharge la photo de profil et la prépare pour reportlab.

    Best-effort : réseau/format invalide -> None, le certificat est alors
    généré sans photo plutôt que d'échouer complètement.
    """
    if not avatar_url:
        return None
    try:
        resp = httpx.get(avatar_url, timeout=5.0, follow_redirects=True)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content)).convert("RGB")
        buf = BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)
        return ImageReader(buf)
    except Exception:
        return None


def _tracked(text: str) -> str:
    """Insère des espaces entre les lettres (effet petites capitales espacées)."""
    return " ".join(text)


def _draw_background(c: canvas.Canvas, width: float, height: float):
    """Bandeau géométrique façon 'montagnes' en bas + accent en haut à droite,
    dans les bleus de marque — inspiré du certificat de référence fourni."""
    # Grand triangle bleu foncé (arrière-plan du bandeau). Volontairement
    # assez bas (crête à ~2cm max) pour ne JAMAIS recouvrir le texte du bas
    # (signatures, sceau, date) — bande décorative fine, pas de hautes
    # montagnes comme sur le modèle de référence (le texte y passait dessus).
    c.setFillColor(NAVY)
    p = c.beginPath()
    p.moveTo(0, 0)
    p.lineTo(width * 0.68, 0)
    p.lineTo(width * 0.22, 2.0 * cm)
    p.close()
    c.drawPath(p, fill=1, stroke=0)

    # Second triangle, bleu vif, se chevauchant pour l'effet "crêtes".
    c.setFillColor(BLUE)
    p = c.beginPath()
    p.moveTo(width * 0.18, 0)
    p.lineTo(width, 0)
    p.lineTo(width * 0.62, 1.7 * cm)
    p.close()
    c.drawPath(p, fill=1, stroke=0)

    # Fine crête pâle pour la profondeur.
    c.setFillColor(BLUE_PALE)
    p = c.beginPath()
    p.moveTo(width * 0.40, 0)
    p.lineTo(width * 0.86, 0)
    p.lineTo(width * 0.62, 0.9 * cm)
    p.close()
    c.drawPath(p, fill=1, stroke=0)

    # Accent triangulaire en haut à droite.
    c.setFillColor(NAVY)
    p = c.beginPath()
    p.moveTo(width, height)
    p.lineTo(width - width * 0.16, height)
    p.lineTo(width, height - height * 0.20)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    c.setFillColor(GOLD)
    p = c.beginPath()
    p.moveTo(width, height)
    p.lineTo(width - width * 0.07, height)
    p.lineTo(width, height - height * 0.09)
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def _draw_seal(c: canvas.Canvas, cx: float, cy: float, year: int):
    """Médaillon doré (façon sceau officiel) avec ruban, sous les signatures."""
    r = 1.3 * cm
    # Rubans qui pendent sous le médaillon.
    c.setFillColor(GOLD_DARK)
    for dx in (-0.45 * cm, 0.45 * cm):
        p = c.beginPath()
        p.moveTo(cx + dx - 0.32 * cm, cy)
        p.lineTo(cx + dx + 0.32 * cm, cy)
        p.lineTo(cx + dx, cy - 1.1 * cm)
        p.close()
        c.drawPath(p, fill=1, stroke=0)
    # Disque du médaillon.
    c.setFillColor(GOLD)
    c.circle(cx, cy, r, fill=1, stroke=0)
    c.setStrokeColor(GOLD_DARK)
    c.setLineWidth(1.4)
    c.circle(cx, cy, r * 0.82, fill=0, stroke=1)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(cx, cy + 2, str(year))
    c.setFont("Helvetica", 6.5)
    c.drawCentredString(cx, cy - 10, "RÉUSSITE")


def generate_certificate(student_name: str, course_title: str, score: int, avatar_url: str = None) -> str:
    os.makedirs(CERT_DIR, exist_ok=True)
    filename = certificate_path(student_name, course_title)

    c = canvas.Canvas(filename, pagesize=landscape(A4))
    width, height = landscape(A4)

    _draw_background(c, width, height)

    # Cadre décoratif : liseré doré (extérieur) + fin trait bleu (intérieur).
    c.setStrokeColor(GOLD)
    c.setLineWidth(3)
    c.roundRect(0.7 * cm, 0.7 * cm, width - 1.4 * cm, height - 1.4 * cm, 10, stroke=1, fill=0)
    c.setStrokeColor(NAVY)
    c.setLineWidth(0.8)
    c.roundRect(1.0 * cm, 1.0 * cm, width - 2.0 * cm, height - 2.0 * cm, 8, stroke=1, fill=0)

    # Logo de la plateforme, centré en haut.
    if LOGO_PATH.exists():
        logo_size = 2.1 * cm
        c.drawImage(
            str(LOGO_PATH), width / 2 - logo_size / 2, height - 3.0 * cm,
            width=logo_size, height=logo_size, mask="auto", preserveAspectRatio=True,
        )

    # Photo de profil (facultative) : médaillon circulaire en haut à gauche.
    avatar = _fetch_avatar(avatar_url)
    if avatar is not None:
        cx, cy, r = 2.6 * cm, height - 2.6 * cm, 1.5 * cm
        c.saveState()
        path = c.beginPath()
        path.circle(cx, cy, r)
        c.clipPath(path, stroke=0)
        c.drawImage(avatar, cx - r, cy - r, width=2 * r, height=2 * r,
                    preserveAspectRatio=True, anchor="c", mask="auto")
        c.restoreState()
        c.setStrokeColor(GOLD)
        c.setLineWidth(2)
        c.circle(cx, cy, r, stroke=1, fill=0)

    # Nom de la plateforme.
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 17)
    c.drawCentredString(width / 2, height - 4.15 * cm, "E-LEARNING UCBC")
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 8.5)
    c.drawCentredString(width / 2, height - 4.65 * cm, _tracked("Plateforme d'apprentissage en ligne"))

    # Titre manuscrit "Certificat".
    c.setFillColor(NAVY)
    c.setFont(SCRIPT_FONT, 56)
    c.drawCentredString(width / 2, height - 6.7 * cm, "Certificat")

    # Pilule "DE RÉUSSITE".
    pill_w, pill_h = 5.6 * cm, 0.85 * cm
    pill_y = height - 7.75 * cm
    c.setFillColor(GOLD)
    c.roundRect(width / 2 - pill_w / 2, pill_y, pill_w, pill_h, pill_h / 2, stroke=0, fill=1)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, pill_y + pill_h / 2 - 4, _tracked("DE RÉUSSITE"))

    # "Décerné avec fierté à".
    c.setFillColor(GRAY)
    c.setFont("Helvetica-Oblique", 12)
    c.drawCentredString(width / 2, height - 9.1 * cm, "Décerné avec fierté à")

    # Nom de l'apprenant + soulignement doré.
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(width / 2, height - 10.3 * cm, student_name)
    name_w = c.stringWidth(student_name, "Helvetica-Bold", 26)
    underline_w = max(name_w + 3 * cm, 8 * cm)
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.2)
    c.line(width / 2 - underline_w / 2, height - 10.65 * cm, width / 2 + underline_w / 2, height - 10.65 * cm)

    # Belle phrase + cours.
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 11.5)
    c.drawCentredString(
        width / 2, height - 11.7 * cm,
        "En reconnaissance de sa persévérance, de son engagement et de sa réussite,",
    )
    c.drawCentredString(
        width / 2, height - 12.35 * cm,
        "pour avoir mené à terme avec succès le parcours de formation :",
    )
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 17)
    c.drawCentredString(width / 2, height - 13.4 * cm, course_title)
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 11)
    c.drawCentredString(width / 2, height - 14.05 * cm, f"avec un score final de {score}%")

    # Signatures (institutionnelles, pas de nom de personne inventé).
    sig_y = 4.3 * cm
    line_w = 5.2 * cm
    left_x = width / 2 - 7.2 * cm
    right_x = width / 2 + 2.0 * cm
    c.setStrokeColor(GRAY)
    c.setLineWidth(0.8)
    c.line(left_x, sig_y, left_x + line_w, sig_y)
    c.line(right_x, sig_y, right_x + line_w, sig_y)
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 9.5)
    c.drawCentredString(left_x + line_w / 2, sig_y - 13, "Formation validée")
    c.setFillColor(NAVY)
    c.setFont(SCRIPT_FONT, 19)
    c.drawCentredString(right_x + line_w / 2, sig_y + 3, "E-Learning UCBC")

    # Médaillon doré, centré entre les deux signatures.
    _draw_seal(c, width / 2, sig_y + 0.35 * cm, date.today().year)

    # Date de délivrance — reste dans la zone blanche, au-dessus du bandeau
    # décoratif du bas (jamais superposée à celui-ci).
    c.setFillColor(GRAY)
    c.setFont("Helvetica-Oblique", 9.5)
    c.drawCentredString(width / 2, 2.6 * cm, f"Délivré le {date.today().strftime('%d/%m/%Y')}")

    c.save()
    return filename
