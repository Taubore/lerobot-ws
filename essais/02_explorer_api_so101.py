"""
Explore les classes disponibles pour le bras SO-101 dans LeRobot officiel.

Objectif :
- vérifier les noms exacts des modules, classes et configurations ;
- éviter d'écrire un script de téléopération basé sur l'ancienne API 0.4.2 ;
- préparer le vrai script de téléopération minimale.
"""

import pkgutil
import lerobot


def afficher_modules_contenant(mot_cle: str) -> None:
    """
    Affiche les modules LeRobot dont le nom contient un mot-clé.

    Cela permet de repérer rapidement où se trouvent les classes SO-101.
    """
    print()
    print("=" * 70)
    print(f"Modules contenant : {mot_cle}")
    print("=" * 70)

    for module in pkgutil.walk_packages(lerobot.__path__, prefix="lerobot."):
        if mot_cle.lower() in module.name.lower():
            print(module.name)


def main() -> None:
    """
    Lance une exploration légère de l'API LeRobot installée.
    """
    print(f"LeRobot chargé depuis : {lerobot.__file__}")

    afficher_modules_contenant("so101")
    afficher_modules_contenant("feetech")
    afficher_modules_contenant("teleop")
    afficher_modules_contenant("follower")
    afficher_modules_contenant("leader")


if __name__ == "__main__":
    main()