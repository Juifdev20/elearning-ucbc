"""
Génère un certificat PDF professionnel quand un apprenant réussit
le quiz final d'un cours.
"""
import os
import re
from pathlib import Path
from datetime import date
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.colors import HexColor
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

# Les PDF sont écrits DANS le dossier assets/ (et non un dossier à part) pour
# que Flet les serve automatiquement en HTTP, à la même adresse en local et
# une fois déployé (un chemin absolu type file:///C:/... ou un lien "assets
# locaux" ne fonctionne QUE si le navigateur tourne sur la même machine que
# le serveur — ça casse dès que l'app est hébergée ailleurs, ex. Render).
BASE_DIR = Path(__file__).resolve().parent.parent
CERT_DIR = BASE_DIR / "assets" / "certificates"


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


def ensure_certificate(student_name: str, course_title: str, score: int) -> str:
    """Génère le certificat s'il n'existe pas encore, retourne son URL de téléchargement."""
    path = certificate_path(student_name, course_title)
    if not os.path.exists(path):
        generate_certificate(student_name, course_title, score)
    return certificate_url(student_name, course_title)


def generate_certificate(student_name: str, course_title: str, score: int) -> str:
    os.makedirs(CERT_DIR, exist_ok=True)
    filename = certificate_path(student_name, course_title)

    c = canvas.Canvas(filename, pagesize=landscape(A4))
    width, height = landscape(A4)

    # Bordure décorative
    c.setStrokeColor(HexColor("#1E3A8A"))
    c.setLineWidth(4)
    c.rect(1 * cm, 1 * cm, width - 2 * cm, height - 2 * cm)
    c.setLineWidth(1)
    c.rect(1.3 * cm, 1.3 * cm, width - 2.6 * cm, height - 2.6 * cm)

    # Titre
    c.setFont("Helvetica-Bold", 34)
    c.setFillColor(HexColor("#1E3A8A"))
    c.drawCentredString(width / 2, height - 4 * cm, "CERTIFICAT DE RÉUSSITE")

    # Sous-titre
    c.setFont("Helvetica", 16)
    c.setFillColor(HexColor("#374151"))
    c.drawCentredString(width / 2, height - 5.3 * cm, "Ce certificat est décerné à")

    # Nom de l'apprenant
    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(HexColor("#111827"))
    c.drawCentredString(width / 2, height - 7 * cm, student_name)

    # Cours
    c.setFont("Helvetica", 16)
    c.setFillColor(HexColor("#374151"))
    c.drawCentredString(width / 2, height - 8.3 * cm, "pour avoir complété avec succès le cours")

    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(HexColor("#1E3A8A"))
    c.drawCentredString(width / 2, height - 9.3 * cm, course_title)

    # Score
    c.setFont("Helvetica", 14)
    c.setFillColor(HexColor("#374151"))
    c.drawCentredString(width / 2, height - 10.5 * cm, f"Score obtenu : {score}%")

    # Date
    c.setFont("Helvetica-Oblique", 12)
    c.drawCentredString(width / 2, 2.5 * cm, f"Délivré le {date.today().strftime('%d/%m/%Y')}")
    c.drawCentredString(width / 2, 2 * cm, "Plateforme E-Learning UCBC")

    c.save()
    return filename
