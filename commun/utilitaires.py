import subprocess
import readline
from time import sleep

FREQUENCE_BIP_LA6_HZ = 1760
FREQUENCE_BIP_LA5_HZ = 880
FREQUENCE_BIP_LA4_HZ = 440

DUREE_BIP_COURT_S = 0.08
DUREE_BIP_MOYEN_S = 0.35
DUREE_BIP_LONG_S = 1.50
PAUSE_ENTRE_BIPS_S = 0.08


def saisir_avec_texte_defaut(invite: str, texte_defaut: str) -> str:
    """
    Saisir un texte en préremplissant la ligne avec une valeur par défaut.
    """

    readline.set_startup_hook(lambda: readline.insert_text(texte_defaut))

    try:
        return input(invite)

    finally:
        readline.set_startup_hook()


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


def jouer_son_debut_episode() -> None:
    """
    Jouer deux bips courts pour marquer le début d'un épisode.
    """

    jouer_bip(FREQUENCE_BIP_LA6_HZ, DUREE_BIP_COURT_S)
    sleep(PAUSE_ENTRE_BIPS_S)
    jouer_bip(FREQUENCE_BIP_LA6_HZ, DUREE_BIP_COURT_S)


def jouer_son_fin_episode() -> None:
    """
    Jouer trois bips courts pour marquer la fin d'un épisode.
    """

    jouer_bip(FREQUENCE_BIP_LA6_HZ, DUREE_BIP_COURT_S)
    sleep(PAUSE_ENTRE_BIPS_S)
    jouer_bip(FREQUENCE_BIP_LA6_HZ, DUREE_BIP_COURT_S)
    sleep(PAUSE_ENTRE_BIPS_S)
    jouer_bip(FREQUENCE_BIP_LA6_HZ, DUREE_BIP_COURT_S)


def jouer_son_fin_episode_avec_changement() -> None:
    """
    Jouer un bip long et 2 bips courts pour marquer la fin d'un épisode qui nécessite 
    un changement dans l'entrainement.
    """

    jouer_bip(FREQUENCE_BIP_LA6_HZ, DUREE_BIP_MOYEN_S)
    sleep(PAUSE_ENTRE_BIPS_S)
    jouer_bip(FREQUENCE_BIP_LA6_HZ, DUREE_BIP_COURT_S)
    sleep(PAUSE_ENTRE_BIPS_S)
    jouer_bip(FREQUENCE_BIP_LA6_HZ, DUREE_BIP_COURT_S)


def jouer_son_reinitialisation() -> None:
    """
    Jouer un bip plus long pour marquer la phase de réinitialisation.
    """

    jouer_bip(FREQUENCE_BIP_LA4_HZ, DUREE_BIP_MOYEN_S)


def jouer_son_fin_entrainement() -> None:
    """
    Jouer un très long bip grave pour signaler la fin complète du script.
    """

    jouer_bip(FREQUENCE_BIP_LA4_HZ, DUREE_BIP_LONG_S)


