import random
from datetime import datetime, timedelta

random.seed(57)

# Listes de données de base
noms = ["MARTIN", "BERNARD", "THOMAS", "PETIT", "ROBERT", "RICHARD", "DURAND", "DUBOIS", "MOREL", "LAURENT", 
        "SIMON", "MICHEL", "LEFEBVRE", "LEROY", "ROUX", "DAVID", "BERTRAND", "MOREAU", "VINCENT", "FOURNIER",
        "GARCIA", "GIRARD", "ANDRE", "LEFEVRE", "MERCIER", "DUPONT", "LAMBERT", "BONNET", "FRANCOIS", "MARTINEZ"]

prenoms_f = ["Jade", "Louise", "Ambre", "Alba", "Emma", "Rose", "Alice", "Romy", "Anna", "Lina", "Léna", "Mia", "Lou", "Julia", "Chloé"]
prenoms_m = ["Gabriel", "Léo", "Raphaël", "Maël", "Louis", "Noah", "Jules", "Arthur", "Adam", "Lucas", "Isaac", "Gabin", "Liam", "Sacha", "Hugo"]

# Classes
secondes = [f"20{i}" for i in range(1, 11)]
premieres = [f"10{i}" for i in range(1, 11)]
terminales = [f"T{i:02d}" for i in range(1, 11)]
toutes_classes = secondes + premieres + terminales

def generer_date_naissance(classe):
    # Détermination de l'année selon le niveau
    if classe in secondes:
        annee = 2010
    elif classe in premieres:
        annee = 2009
    else:
        annee = 2008
    
    # Génération d'un jour aléatoire dans l'année
    debut_annee = datetime(annee, 1, 1)
    jours_aleatoires = random.randint(0, 364)
    date_naiss = debut_annee + timedelta(days=jours_aleatoires)
    return date_naiss.strftime("%d/%m/%Y")

# Header CSV
print("Nom,Prenom,Sexe,Classe,Date_Naissance")

# Génération des 2000 lignes
for _ in range(2000):
    sexe = random.choice(["F", "M"])
    nom = random.choice(noms)
    prenom = random.choice(prenoms_f) if sexe == "F" else random.choice(prenoms_m)
    classe = random.choice(toutes_classes)
    date_n = generer_date_naissance(classe)
    
    print(f"{nom},{prenom},{sexe},{classe},{date_n}")