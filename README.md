# UNSS — Lycée MNS · Application de gestion

Application web Python (Flask) pour la gestion de l'UNSS.  
**Aucune base SQL** — stockage via un fichier `data/unss_data.json`.

---

## Installation rapide

### Pré-requis
- Python 3.10 ou supérieur  
- pip

### Étapes

```bash
# 1. Cloner / décompresser le dossier unss_app
cd unss_app

# 2. Créer un environnement virtuel (recommandé)
python -m venv .venv
# Windows :
.venv\Scripts\activate
# macOS / Linux :
source .venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Lancer l'application
python app.py
```

Ouvrir dans le navigateur : **http://localhost:5000**

---

## Générer le CSV des élèves

```bash
python mns_unss_eleves.py > eleves.csv
```

Puis l'importer via l'onglet **Import** de l'application.

---

## Structure du projet

```
unss_app/
├── app.py               # Serveur Flask + API REST
├── mns_unss_eleves.py   # Générateur CSV fourni
├── requirements.txt
├── README.md
├── templates/
│   └── index.html       # Interface web complète (SPA)
└── data/
    └── unss_data.json   # Données persistantes (créé automatiquement)
```

---

## Fonctionnalités

### Élèves
- Import CSV (drag & drop ou clic)
- Ajout d'un élève retardataire
- Recherche par début de nom
- Filtres : niveau, classe, carte Jeun'EST, photo, sport
- Modification individuelle (modale) ou en lot (sélection multiple)
- Édition inline de la carte Jeun'EST (clic direct)
- Basculement rapide de l'autorisation photo (clic sur badge)
- Tri sur toutes les colonnes
- Statistiques dynamiques
- Impression (Ctrl+P)

### Sports
- Ajout / suppression de sports
- Inscription d'élèves (recherche par nom + filtre classe)
- Désinscription individuelle
- 7 champs booléens par sport (QR_CODE, FICHE, Cotisation, Journées 1-4)
- Renommage des champs (BONUS)
- Cochage/décochage inline

### Données
- Persistance JSON dans `data/unss_data.json`
- Chaque élève a un identifiant unique
- Un élève peut être inscrit à plusieurs sports simultanément
