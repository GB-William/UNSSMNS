"""
Configuration globale de l'application UNSS - Lycée MNS
"""

from pathlib import Path

APP_DIR = Path(__file__).parent
DATA_FILE = APP_DIR / "data" / "unss_data.json"
UPLOAD_DIR = APP_DIR / "data"

COTISATION_DEFAUT = 10.0
CHAMPS_SPORT_DEFAUT = [
    "QR_CODE", "FICHE", "Cotisation", "Journée 1", "Journée 2", "Journée 3", "Journée 4"
]
