'''
Pour vérifier que les dépendances nécessaires sont bien installées.
Il tente d'importer chaque module de la liste et affichera si le module est présent ou absent. 
'''
import importlib.util
import sys

modules = [
    "datasets",
    "pyarrow",
    "av",
    "accelerate",
    "scservo_sdk",
    "rerun",
    "lerobot.motors.feetech.feetech",
]

print(f"Python : {sys.executable}")
print()

for module in modules:
    resultat = importlib.util.find_spec(module)
    etat = "OK" if resultat is not None else "absent"
    print(f"{module:35} : {etat}")