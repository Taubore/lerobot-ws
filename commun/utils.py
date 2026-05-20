'''
Regroupe un ensemble de fonctions utilitaires génériques qu'il est possible d'utiliser dans une
multitude d'autres projets.
'''

import subprocess
import readline

def jouer_bip(frequence_hz: int, duree_s: float) -> None:
    """
    Jouer un bip sonore court avec `ffplay`.

    Le son est généré directement par FFmpeg avec un signal sinusoïdal.
    Si `ffplay` n'est pas disponible ou si l'audio échoue, le script continue.
    """

    commande = [
        "ffplay",
        "-nodisp",
        "-autoexit",
        "-loglevel",
        "quiet",
        "-f",
        "lavfi",
        f"sine=frequency={frequence_hz}:duration={duree_s}",
    ]

    try:
        subprocess.run(
            commande,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
        )

    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def saisir_avec_texte_defaut(invite: str, texte_defaut: str) -> str:
    """
    Saisir un texte en préremplissant la ligne avec une valeur par défaut.
    """

    readline.set_startup_hook(lambda: readline.insert_text(texte_defaut))

    try:
        return input(invite)

    finally:
        readline.set_startup_hook()
