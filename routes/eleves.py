"""
Routes API - Élèves
Gestion des élèves : liste, ajout, modification, suppression, import CSV
"""

import subprocess
import sys

from flask import Blueprint, jsonify, request

from config import APP_DIR, COTISATION_DEFAUT
from persistence import charger_donnees, generer_id, sauvegarder_donnees

bp = Blueprint("eleves", __name__)


# ---------------------------------------------------------------------------
# Helpers
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
# Routes
# ---------------------------------------------------------------------------

@bp.route("/api/eleves", methods=["GET"])
def lister_eleves():
    """Retourne la liste des élèves avec filtres optionnels."""
    donnees = charger_donnees()
    eleves = donnees.get("eleves", {})

    recherche = request.args.get("q", "").lower()
    classe_filtre = request.args.get("classe", "")
    niveau_filtre = request.args.get("niveau", "")
    sport_filtre = request.args.get("sport", "")
    carte_filtre = request.args.get("carte", "")   # "oui" | "non" | ""
    photo_filtre = request.args.get("photo", "")   # "oui" | "non" | ""

    resultats = []
    for eleve_id, eleve in eleves.items():
        if recherche and not eleve["nom"].lower().startswith(recherche):
            continue
        if classe_filtre and eleve["classe"] != classe_filtre:
            continue
        if niveau_filtre:
            classe = eleve["classe"]
            if niveau_filtre == "seconde" and not classe.startswith("20"):
                continue
            if niveau_filtre == "premiere" and not classe.startswith("10"):
                continue
            if niveau_filtre == "terminale" and not classe.startswith("T"):
                continue
        if sport_filtre and sport_filtre not in eleve.get("sports", []):
            continue
        if carte_filtre == "oui" and not eleve.get("carte_jeunest", ""):
            continue
        if carte_filtre == "non" and eleve.get("carte_jeunest", ""):
            continue
        if photo_filtre == "oui" and not eleve.get("autorisation_photo", False):
            continue
        if photo_filtre == "non" and eleve.get("autorisation_photo", False):
            continue

        resultats.append({"id": eleve_id, **eleve})

    resultats.sort(key=lambda e: (e["nom"], e["prenom"]))
    return jsonify(resultats)


@bp.route("/api/eleves", methods=["POST"])
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


@bp.route("/api/eleves/<eleve_id>", methods=["PATCH"])
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


@bp.route("/api/eleves/<eleve_id>", methods=["DELETE"])
def supprimer_eleve(eleve_id: str):
    """Supprime un élève et le retire de tous les sports."""
    donnees = charger_donnees()
    if eleve_id not in donnees["eleves"]:
        return jsonify({"erreur": "Élève introuvable"}), 404

    for sport_data in donnees.get("sports", {}).values():
        sport_data.get("inscrits", {}).pop(eleve_id, None)

    del donnees["eleves"][eleve_id]
    sauvegarder_donnees(donnees)
    return jsonify({"ok": True})


@bp.route("/api/eleves/batch", methods=["PATCH"])
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


@bp.route("/api/import", methods=["POST"])
def importer_eleves():
    """Importe des élèves depuis un fichier CSV uploadé."""
    if "fichier" not in request.files:
        return jsonify({"erreur": "Aucun fichier fourni"}), 400

    fichier = request.files["fichier"]
    contenu = fichier.read().decode("utf-8", errors="replace")
    nb, erreurs = importer_csv_eleves(contenu)
    return jsonify({"importes": nb, "erreurs": erreurs})


@bp.route("/api/generer_eleves", methods=["POST"])
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
