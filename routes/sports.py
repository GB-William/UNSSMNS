"""
Routes API - Sports
Gestion des sports : liste, création, suppression, inscriptions, champs
"""

from flask import Blueprint, jsonify, request

from config import CHAMPS_SPORT_DEFAUT
from persistence import charger_donnees, sauvegarder_donnees

bp = Blueprint("sports", __name__)


@bp.route("/api/sports", methods=["GET"])
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


@bp.route("/api/sports", methods=["POST"])
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


@bp.route("/api/sports/<nom_sport>", methods=["DELETE"])
def supprimer_sport(nom_sport: str):
    """Supprime un sport et toutes ses inscriptions."""
    donnees = charger_donnees()
    if nom_sport not in donnees.get("sports", {}):
        return jsonify({"erreur": "Sport introuvable"}), 404

    del donnees["sports"][nom_sport]
    sauvegarder_donnees(donnees)
    return jsonify({"ok": True})


@bp.route("/api/sports/<nom_sport>/inscrits", methods=["GET"])
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


@bp.route("/api/sports/<nom_sport>/inscrire", methods=["POST"])
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
            eleve_sports = donnees["eleves"][eleve_id].setdefault("sports", [])
            if nom_sport not in eleve_sports:
                eleve_sports.append(nom_sport)
            inscrits_count += 1

    sauvegarder_donnees(donnees)
    return jsonify({"inscrits": inscrits_count})


@bp.route("/api/sports/<nom_sport>/desinscrire/<eleve_id>", methods=["DELETE"])
def desinscrire_eleve_sport(nom_sport: str, eleve_id: str):
    """Désinscrit un élève d'un sport."""
    donnees = charger_donnees()
    sport = donnees.get("sports", {}).get(nom_sport)
    if sport is None:
        return jsonify({"erreur": "Sport introuvable"}), 404

    sport.get("inscrits", {}).pop(eleve_id, None)

    eleve = donnees.get("eleves", {}).get(eleve_id)
    if eleve and nom_sport in eleve.get("sports", []):
        eleve["sports"].remove(nom_sport)

    sauvegarder_donnees(donnees)
    return jsonify({"ok": True})


@bp.route("/api/sports/<nom_sport>/inscrits/<eleve_id>", methods=["PATCH"])
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


@bp.route("/api/sports/<nom_sport>/champs", methods=["PUT"])
def renommer_champs_sport(nom_sport: str):
    """Renomme les champs d'un sport (max 7)."""
    donnees = charger_donnees()
    sport = donnees.get("sports", {}).get(nom_sport)
    if sport is None:
        return jsonify({"erreur": "Sport introuvable"}), 404

    payload = request.get_json(force=True)
    nouveaux_champs = payload.get("champs", [])[:7]
    anciens_champs = sport.get("champs", CHAMPS_SPORT_DEFAUT[:])

    for eleve_id, champs_vals in sport.get("inscrits", {}).items():
        nouvelles_vals = {}
        for i, nouveau in enumerate(nouveaux_champs):
            ancien = anciens_champs[i] if i < len(anciens_champs) else None
            nouvelles_vals[nouveau] = champs_vals.get(ancien, False) if ancien else False
        sport["inscrits"][eleve_id] = nouvelles_vals

    sport["champs"] = nouveaux_champs
    sauvegarder_donnees(donnees)
    return jsonify({"champs": nouveaux_champs})
