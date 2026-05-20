'''
Regroupe un ensemble de fonctions utilitaires propres à ce projet. C'est à dire utile pour plus
d'un script, mais avec des spécificités à ce projet.
'''

from time import sleep
from commun import utils

FREQUENCE_BIP_LA6_HZ = 1760
FREQUENCE_BIP_LA5_HZ = 880
FREQUENCE_BIP_LA4_HZ = 440

DUREE_BIP_COURT_S = 0.08
DUREE_BIP_MOYEN_S = 0.35
DUREE_BIP_LONG_S = 1.50
PAUSE_ENTRE_BIPS_S = 0.08


def jouer_son_debut_episode() -> None:
    """
    Jouer deux bips courts pour marquer le début d'un épisode.
    """

    utils.jouer_bip(FREQUENCE_BIP_LA6_HZ, DUREE_BIP_COURT_S)
    sleep(PAUSE_ENTRE_BIPS_S)
    utils.jouer_bip(FREQUENCE_BIP_LA6_HZ, DUREE_BIP_COURT_S)


def jouer_son_fin_episode() -> None:
    """
    Jouer trois bips courts pour marquer la fin d'un épisode.
    """

    utils.jouer_bip(FREQUENCE_BIP_LA6_HZ, DUREE_BIP_COURT_S)
    sleep(PAUSE_ENTRE_BIPS_S)
    utils.jouer_bip(FREQUENCE_BIP_LA6_HZ, DUREE_BIP_COURT_S)
    sleep(PAUSE_ENTRE_BIPS_S)
    utils.jouer_bip(FREQUENCE_BIP_LA6_HZ, DUREE_BIP_COURT_S)


def jouer_son_reinitialisation() -> None:
    """
    Jouer un bip plus long pour marquer la phase de réinitialisation.
    """

    utils.jouer_bip(FREQUENCE_BIP_LA4_HZ, DUREE_BIP_MOYEN_S)


def jouer_son_annulation_episode() -> None:
    """
    Jouer un motif grave-aigu-grave pour signaler l'annulation d'un épisode.
    """

    utils.jouer_bip(FREQUENCE_BIP_LA4_HZ, DUREE_BIP_COURT_S)
    sleep(PAUSE_ENTRE_BIPS_S)
    utils.jouer_bip(FREQUENCE_BIP_LA4_HZ, DUREE_BIP_COURT_S)
    sleep(PAUSE_ENTRE_BIPS_S)
    utils.jouer_bip(FREQUENCE_BIP_LA4_HZ, DUREE_BIP_COURT_S)


def jouer_son_fin_dataset() -> None:
    """
    Jouer un très long bip grave pour signaler la fin complète du script.
    """

    utils.jouer_bip(FREQUENCE_BIP_LA4_HZ, DUREE_BIP_LONG_S)

