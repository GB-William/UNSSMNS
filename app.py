"""
Application de gestion UNSS - Lycée MNS
Serveur Flask principal - point d'entrée
"""

from flask import Flask, render_template

from config import UPLOAD_DIR
from routes import classes, eleves, sports

app = Flask(__name__)

# Enregistrement des Blueprints
app.register_blueprint(eleves.bp)
app.register_blueprint(sports.bp)
app.register_blueprint(classes.bp)


@app.route("/")
def index():
    """Sert la page HTML principale."""
    return render_template("index.html")


if __name__ == "__main__":
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=5000)
