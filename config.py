import os
from pathlib import Path
from dotenv import load_dotenv

# On charge le .env avec un chemin absolu (basé sur l'emplacement de ce fichier),
# pour que ça fonctionne peu importe le dossier depuis lequel "flet run" est lancé.
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

if not SUPABASE_URL or not SUPABASE_KEY:
    print("⚠️  ATTENTION : SUPABASE_URL ou SUPABASE_KEY est vide.")
    print(f"    Fichier .env recherché ici : {BASE_DIR / '.env'}")
    print(f"    Ce fichier existe ? {(BASE_DIR / '.env').exists()}")

APP_NAME = "E-Learning UCBC"
PASS_SCORE_DEFAULT = 70  # % minimum pour réussir un quiz et obtenir le brevet