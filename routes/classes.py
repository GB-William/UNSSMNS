"""
Routes API - Classes
Liste des classes présentes dans les données
"""

from flask import Blueprint, jsonify

from persistence import charger_donnees

bp = Blueprint("classes", __name__)


@bp.route("/api/classes", methods=["GET"])
def lister_classes():
    """Retourne la liste des classes présentes dans les données."""
    donnees = charger_donnees()
    classes = sorted({e["classe"] for e in donnees.get("eleves", {}).values()})
    return jsonify(classes)
