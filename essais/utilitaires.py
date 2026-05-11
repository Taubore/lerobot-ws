import subprocess
from time import sleep

FREQUENCE_BIP_COURT_HZ = 880
FREQUENCE_BIP_LONG_HZ = 440

DUREE_BIP_COURT_S = 0.08
DUREE_BIP_LONG_S = 0.35
PAUSE_ENTRE_BIPS_S = 0.08


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


def jouer_bips_courts() -> None:
    """
    Jouer deux bips courts pour marquer le début ou la fin d'un épisode.
    """

    jouer_bip(FREQUENCE_BIP_COURT_HZ, DUREE_BIP_COURT_S)
    sleep(PAUSE_ENTRE_BIPS_S)
    jouer_bip(FREQUENCE_BIP_COURT_HZ, DUREE_BIP_COURT_S)


def jouer_bip_reinitialisation() -> None:
    """
    Jouer un bip plus long pour marquer la phase de réinitialisation.
    """

    jouer_bip(FREQUENCE_BIP_LONG_HZ, DUREE_BIP_LONG_S)


def jouer_bips_fin_cycle() -> None:
    """
    Jouer deux bips longs pour signaler la fin complète du script.
    """

    jouer_bip(FREQUENCE_BIP_LONG_HZ, DUREE_BIP_LONG_S)
    sleep(PAUSE_ENTRE_BIPS_S)
    jouer_bip(FREQUENCE_BIP_LONG_HZ, DUREE_BIP_LONG_S)
