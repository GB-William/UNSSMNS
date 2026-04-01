"""
Application de gestion UNSS - Lycée MNS
Serveur Flask principal
"""

import json
import os
import random
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, jsonify, render_template, request

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

APP_DIR = Path(__file__).parent
DATA_FILE = APP_DIR / "data" / "unss_data.json"
UPLOAD_DIR = APP_DIR / "data"

COTISATION_DEFAUT = 10.0
CHAMPS_SPORT_DEFAUT = [
    "QR_CODE", "FICHE", "Cotisation", "Journée 1", "Journée 2", "Journée 3", "Journée 4"
]

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Persistance JSON
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Import CSV des élèves
# ---------------------------------------------------------------------------

def creer_eleve(nom: str, prenom: str, sexe: str, classe: str, date_naissance: str) -> dict:
    """Crée un dictionnaire élève avec les valeurs par défaut."""
    return {
        "nom": nom.strip().upper(),
        "prenom": prenom.strip().capitalize(),
        "sexe": sexe.strip().upper(),
        "classe": classe.strip().upper(),
        "date_naissance": date_naissance.strip(),
        "carte_jeunest": "",
        "autorisation_photo": False,
        "cotisation": COTISATION_DEFAUT,
        "sports": [],
    }


def importer_csv_eleves(contenu_csv: str) -> tuple[int, list[str]]:
    """
    Importe les élèves depuis un contenu CSV.
    Retourne (nombre_importés, liste_erreurs).
    """
    donnees = charger_donnees()
    compteur = 0
    erreurs = []

    lignes = contenu_csv.strip().splitlines()
    if not lignes:
        return 0, ["Fichier vide"]

    # Ignorer l'entête
    debut = 1 if lignes[0].lower().startswith("nom") else 0

    for num_ligne, ligne in enumerate(lignes[debut:], start=debut + 1):
        parts = ligne.strip().split(",")
        if len(parts) < 5:
            erreurs.append(f"Ligne {num_ligne} ignorée (champs insuffisants) : {ligne}")
            continue
        nom, prenom, sexe, classe, date_naissance = parts[:5]
        eleve_id = generer_id(donnees)
        donnees["eleves"][eleve_id] = creer_eleve(nom, prenom, sexe, classe, date_naissance)
        compteur += 1

    sauvegarder_donnees(donnees)
    return compteur, erreurs


# ---------------------------------------------------------------------------
# Routes API — Élèves
# ---------------------------------------------------------------------------

@app.route("/api/eleves", methods=["GET"])
def lister_eleves():
    """Retourne la liste des élèves avec filtres optionnels."""
    donnees = charger_donnees()
    eleves = donnees.get("eleves", {})

    # Paramètres de filtre
    recherche = request.args.get("q", "").lower()
    classe_filtre = request.args.get("classe", "")
    niveau_filtre = request.args.get("niveau", "")
    sport_filtre = request.args.get("sport", "")
    carte_filtre = request.args.get("carte", "")  # "oui" | "non" | ""
    photo_filtre = request.args.get("photo", "")  # "oui" | "non" | ""

    resultats = []
    for eleve_id, eleve in eleves.items():
        # Filtre recherche textuelle (début du nom)
        if recherche and not eleve["nom"].lower().startswith(recherche):
            continue
        # Filtre classe exacte
        if classe_filtre and eleve["classe"] != classe_filtre:
            continue
        # Filtre niveau (20x=seconde, 10x=premiere, Txx=terminale)
        if niveau_filtre:
            classe = eleve["classe"]
            if niveau_filtre == "seconde" and not classe.startswith("20"):
                continue
            if niveau_filtre == "premiere" and not classe.startswith("10"):
                continue
            if niveau_filtre == "terminale" and not classe.startswith("T"):
                continue
        # Filtre sport
        if sport_filtre and sport_filtre not in eleve.get("sports", []):
            continue
        # Filtre carte_jeunest
        if carte_filtre == "oui" and not eleve.get("carte_jeunest", ""):
            continue
        if carte_filtre == "non" and eleve.get("carte_jeunest", ""):
            continue
        # Filtre photo
        if photo_filtre == "oui" and not eleve.get("autorisation_photo", False):
            continue
        if photo_filtre == "non" and eleve.get("autorisation_photo", False):
            continue

        resultats.append({"id": eleve_id, **eleve})

    # Tri par nom
    resultats.sort(key=lambda e: (e["nom"], e["prenom"]))
    return jsonify(resultats)


@app.route("/api/eleves", methods=["POST"])
def ajouter_eleve():
    """Ajoute un seul élève manuellement."""
    payload = request.get_json(force=True)
    champs_requis = ("nom", "prenom", "sexe", "classe", "date_naissance")
    for champ in champs_requis:
        if not payload.get(champ):
            return jsonify({"erreur": f"Champ requis manquant : {champ}"}), 400

    donnees = charger_donnees()
    eleve_id = generer_id(donnees)
    donnees["eleves"][eleve_id] = creer_eleve(
        payload["nom"],
        payload["prenom"],
        payload["sexe"],
        payload["classe"],
        payload["date_naissance"],
    )
    sauvegarder_donnees(donnees)
    return jsonify({"id": eleve_id, **donnees["eleves"][eleve_id]}), 201


@app.route("/api/eleves/<eleve_id>", methods=["PATCH"])
def modifier_eleve(eleve_id: str):
    """Modifie les champs d'un élève existant."""
    donnees = charger_donnees()
    if eleve_id not in donnees["eleves"]:
        return jsonify({"erreur": "Élève introuvable"}), 404

    payload = request.get_json(force=True)
    champs_modifiables = {
        "carte_jeunest", "autorisation_photo", "cotisation",
        "nom", "prenom", "classe", "date_naissance", "sexe",
    }
    for champ, valeur in payload.items():
        if champ in champs_modifiables:
            donnees["eleves"][eleve_id][champ] = valeur

    sauvegarder_donnees(donnees)
    return jsonify({"id": eleve_id, **donnees["eleves"][eleve_id]})


@app.route("/api/eleves/<eleve_id>", methods=["DELETE"])
def supprimer_eleve(eleve_id: str):
    """Supprime un élève et le retire de tous les sports."""
    donnees = charger_donnees()
    if eleve_id not in donnees["eleves"]:
        return jsonify({"erreur": "Élève introuvable"}), 404

    # Retirer l'élève de tous les sports
    for sport_data in donnees.get("sports", {}).values():
        sport_data.get("inscrits", {}).pop(eleve_id, None)

    del donnees["eleves"][eleve_id]
    sauvegarder_donnees(donnees)
    return jsonify({"ok": True})


@app.route("/api/eleves/batch", methods=["PATCH"])
def modifier_eleves_batch():
    """Modifie plusieurs élèves d'un coup (sélection par classe/niveau)."""
    donnees = charger_donnees()
    payload = request.get_json(force=True)
    ids = payload.get("ids", [])
    modifications = payload.get("modifications", {})

    champs_modifiables = {"carte_jeunest", "autorisation_photo", "cotisation"}
    for eleve_id in ids:
        if eleve_id in donnees["eleves"]:
            for champ, valeur in modifications.items():
                if champ in champs_modifiables:
                    donnees["eleves"][eleve_id][champ] = valeur

    sauvegarder_donnees(donnees)
    return jsonify({"modifies": len(ids)})


@app.route("/api/import", methods=["POST"])
def importer_eleves():
    """Importe des élèves depuis un fichier CSV uploadé."""
    if "fichier" not in request.files:
        return jsonify({"erreur": "Aucun fichier fourni"}), 400

    fichier = request.files["fichier"]
    contenu = fichier.read().decode("utf-8", errors="replace")
    nb, erreurs = importer_csv_eleves(contenu)
    return jsonify({"importes": nb, "erreurs": erreurs})


@app.route("/api/generer_eleves", methods=["POST"])
def generer_eleves():
    """Génère des élèves en exécutant mns_unss_eleves.py et importe le résultat CSV."""
    script = APP_DIR / "mns_unss_eleves.py"
    if not script.exists():
        return jsonify({"erreur": "mns_unss_eleves.py introuvable"}), 404

    try:
        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(script)],
            capture_output=True, text=True, encoding="utf-8", timeout=30
        )
    except subprocess.TimeoutExpired:
        return jsonify({"erreur": "Timeout : génération trop longue"}), 500

    if result.returncode != 0 or not result.stdout:
        return jsonify({"erreur": result.stderr or "Le script n'a produit aucune sortie"}), 500

    nb, erreurs = importer_csv_eleves(result.stdout)
    return jsonify({"importes": nb, "erreurs": erreurs})


# ---------------------------------------------------------------------------
# Routes API — Sports
# ---------------------------------------------------------------------------

@app.route("/api/sports", methods=["GET"])
def lister_sports():
    """Retourne la liste des sports avec le nombre d'inscrits."""
    donnees = charger_donnees()
    sports = donnees.get("sports", {})
    resultats = [
        {
            "nom": nom,
            "nb_inscrits": len(sport.get("inscrits", {})),
        }
        for nom, sport in sports.items()
    ]
    resultats.sort(key=lambda s: s["nom"])
    return jsonify(resultats)


@app.route("/api/sports", methods=["POST"])
def ajouter_sport():
    """Crée un nouveau sport."""
    payload = request.get_json(force=True)
    nom = payload.get("nom", "").strip()
    if not nom:
        return jsonify({"erreur": "Nom du sport requis"}), 400

    donnees = charger_donnees()
    if nom in donnees.get("sports", {}):
        return jsonify({"erreur": "Ce sport existe déjà"}), 409

    donnees.setdefault("sports", {})[nom] = {
        "inscrits": {},
        "champs": donnees.get("champs_sport", CHAMPS_SPORT_DEFAUT[:]),
    }
    sauvegarder_donnees(donnees)
    return jsonify({"nom": nom}), 201


@app.route("/api/sports/<nom_sport>", methods=["DELETE"])
def supprimer_sport(nom_sport: str):
    """Supprime un sport et toutes ses inscriptions."""
    donnees = charger_donnees()
    if nom_sport not in donnees.get("sports", {}):
        return jsonify({"erreur": "Sport introuvable"}), 404

    del donnees["sports"][nom_sport]
    sauvegarder_donnees(donnees)
    return jsonify({"ok": True})


@app.route("/api/sports/<nom_sport>/inscrits", methods=["GET"])
def lister_inscrits_sport(nom_sport: str):
    """Retourne les élèves inscrits à un sport avec leurs champs."""
    donnees = charger_donnees()
    sport = donnees.get("sports", {}).get(nom_sport)
    if sport is None:
        return jsonify({"erreur": "Sport introuvable"}), 404

    eleves = donnees.get("eleves", {})
    champs = sport.get("champs", CHAMPS_SPORT_DEFAUT[:])
    inscrits = sport.get("inscrits", {})

    recherche = request.args.get("q", "").lower()

    resultats = []
    for eleve_id, champs_vals in inscrits.items():
        eleve = eleves.get(eleve_id)
        if not eleve:
            continue
        if recherche and not eleve["nom"].lower().startswith(recherche):
            continue
        resultats.append({
            "id": eleve_id,
            "nom": eleve["nom"],
            "prenom": eleve["prenom"],
            "classe": eleve["classe"],
            "champs": champs_vals,
        })

    resultats.sort(key=lambda e: (e["nom"], e["prenom"]))
    return jsonify({"inscrits": resultats, "champs": champs})


@app.route("/api/sports/<nom_sport>/inscrire", methods=["POST"])
def inscrire_eleve_sport(nom_sport: str):
    """Inscrit un ou plusieurs élèves à un sport."""
    donnees = charger_donnees()
    sport = donnees.get("sports", {}).get(nom_sport)
    if sport is None:
        return jsonify({"erreur": "Sport introuvable"}), 404

    payload = request.get_json(force=True)
    ids = payload.get("ids", [])
    champs = sport.get("champs", CHAMPS_SPORT_DEFAUT[:])

    inscrits_count = 0
    for eleve_id in ids:
        if eleve_id not in donnees.get("eleves", {}):
            continue
        if eleve_id not in sport["inscrits"]:
            sport["inscrits"][eleve_id] = {c: False for c in champs}
            # Ajouter le sport dans la liste de l'élève
            eleve_sports = donnees["eleves"][eleve_id].setdefault("sports", [])
            if nom_sport not in eleve_sports:
                eleve_sports.append(nom_sport)
            inscrits_count += 1

    sauvegarder_donnees(donnees)
    return jsonify({"inscrits": inscrits_count})


@app.route("/api/sports/<nom_sport>/desinscrire/<eleve_id>", methods=["DELETE"])
def desinscrire_eleve_sport(nom_sport: str, eleve_id: str):
    """Désinscrit un élève d'un sport."""
    donnees = charger_donnees()
    sport = donnees.get("sports", {}).get(nom_sport)
    if sport is None:
        return jsonify({"erreur": "Sport introuvable"}), 404

    sport.get("inscrits", {}).pop(eleve_id, None)

    # Retirer le sport de la liste de l'élève
    eleve = donnees.get("eleves", {}).get(eleve_id)
    if eleve and nom_sport in eleve.get("sports", []):
        eleve["sports"].remove(nom_sport)

    sauvegarder_donnees(donnees)
    return jsonify({"ok": True})


@app.route("/api/sports/<nom_sport>/inscrits/<eleve_id>", methods=["PATCH"])
def modifier_champs_sport(nom_sport: str, eleve_id: str):
    """Modifie les champs boolean d'un élève dans un sport."""
    donnees = charger_donnees()
    sport = donnees.get("sports", {}).get(nom_sport)
    if sport is None or eleve_id not in sport.get("inscrits", {}):
        return jsonify({"erreur": "Inscription introuvable"}), 404

    payload = request.get_json(force=True)
    for champ, valeur in payload.items():
        sport["inscrits"][eleve_id][champ] = valeur

    sauvegarder_donnees(donnees)
    return jsonify(sport["inscrits"][eleve_id])


@app.route("/api/sports/<nom_sport>/champs", methods=["PUT"])
def renommer_champs_sport(nom_sport: str):
    """Renomme les champs d'un sport (max 7)."""
    donnees = charger_donnees()
    sport = donnees.get("sports", {}).get(nom_sport)
    if sport is None:
        return jsonify({"erreur": "Sport introuvable"}), 404

    payload = request.get_json(force=True)
    nouveaux_champs = payload.get("champs", [])[:7]

    anciens_champs = sport.get("champs", CHAMPS_SPORT_DEFAUT[:])

    # Migrer les données existantes
    for eleve_id, champs_vals in sport.get("inscrits", {}).items():
        nouvelles_vals = {}
        for i, nouveau in enumerate(nouveaux_champs):
            ancien = anciens_champs[i] if i < len(anciens_champs) else None
            nouvelles_vals[nouveau] = champs_vals.get(ancien, False) if ancien else False
        sport["inscrits"][eleve_id] = nouvelles_vals

    sport["champs"] = nouveaux_champs
    sauvegarder_donnees(donnees)
    return jsonify({"champs": nouveaux_champs})


# ---------------------------------------------------------------------------
# Routes API — Classes
# ---------------------------------------------------------------------------

@app.route("/api/classes", methods=["GET"])
def lister_classes():
    """Retourne la liste des classes présentes dans les données."""
    donnees = charger_donnees()
    classes = sorted({e["classe"] for e in donnees.get("eleves", {}).values()})
    return jsonify(classes)


# ---------------------------------------------------------------------------
# Route principale
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Sert la page HTML principale."""
    return render_template("index.html")


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=5000)
