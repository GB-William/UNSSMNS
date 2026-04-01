"""
Persistance des données - lecture/écriture JSON
"""

import json
import random

from config import CHAMPS_SPORT_DEFAUT, DATA_FILE, UPLOAD_DIR


def charger_donnees() -> dict:
    """Charge les données depuis le fichier JSON."""
    if not DATA_FILE.exists():
        return {"eleves": {}, "sports": {}, "champs_sport": CHAMPS_SPORT_DEFAUT[:]}
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"eleves": {}, "sports": {}, "champs_sport": CHAMPS_SPORT_DEFAUT[:]}


def sauvegarder_donnees(donnees: dict) -> None:
    """Sauvegarde les données dans le fichier JSON."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(donnees, f, ensure_ascii=False, indent=2)


def generer_id(donnees: dict) -> str:
    """Génère un identifiant unique pour un élève."""
    existants = set(donnees.get("eleves", {}).keys())
    while True:
        nouvel_id = f"elv_{random.randint(100000, 999999)}"
        if nouvel_id not in existants:
            return nouvel_id
