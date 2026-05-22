'''
Regroupe un ensemble de fonctions utilitaires génériques qu'il est possible d'utiliser dans une
multitude d'autres projets.
'''

import subprocess
import sys
import termios
import tty
from typing import Any

TOUCHE_ENTREE = ("\r", "\n")
TOUCHE_ECHAP = "\x1b"
TOUCHES_RETOUR = ("\x7f", "\b")
TOUCHE_SUPPRESSION = "3"
TOUCHE_CTRL_C = "\x03"
TOUCHE_CTRL_D = "\x04"
SEQUENCE_CONTROLE = "["
SEQUENCE_GAUCHE = "D"
SEQUENCE_DROITE = "C"
SEQUENCE_DEBUT = "H"
SEQUENCE_FIN = "F"
FIN_SEQUENCE = "~"


def _restaurer_terminal_interactif() -> None:
    """
    Remettre le terminal dans un état adapté aux saisies ligne par ligne.

    Certains écouteurs clavier désactivent l'écho ou le mode canonique. Si le script est
    interrompu dans cet état, `input()` reçoit encore les valeurs, mais l'utilisateur ne voit ni
    les caractères saisis ni le retour de ligne.
    """

    if not sys.stdin.isatty():
        return

    descripteur = sys.stdin.fileno()
    attributs: list[Any] = termios.tcgetattr(descripteur)
    nouveaux_attributs = attributs.copy()

    nouveaux_attributs[0] = nouveaux_attributs[0] | termios.ICRNL
    nouveaux_attributs[1] = nouveaux_attributs[1] | termios.OPOST | termios.ONLCR
    nouveaux_attributs[3] = (
        nouveaux_attributs[3]
        | termios.ECHO
        | termios.ECHONL
        | termios.ICANON
        | termios.IEXTEN
        | termios.ISIG
    )

    termios.tcsetattr(descripteur, termios.TCSADRAIN, nouveaux_attributs)


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

    _restaurer_terminal_interactif()

    if not sys.stdin.isatty():
        texte = input(f"{invite}[{texte_defaut}] ").strip()

        if texte:
            return texte

        return texte_defaut

    return _saisir_ligne_modifiable(invite, texte_defaut).strip() or texte_defaut


def saisir_ligne(invite: str) -> str:
    """
    Saisir une ligne de texte après remise en état du terminal interactif.
    """

    _restaurer_terminal_interactif()
    return input(invite)


def _saisir_ligne_modifiable(invite: str, texte_initial: str) -> str:
    """
    Lire une ligne préremplie sans dépendre de `readline`.
    """

    descripteur = sys.stdin.fileno()
    attributs = termios.tcgetattr(descripteur)
    caracteres = list(texte_initial)
    position = len(caracteres)

    sys.stdout.write(invite + texte_initial)
    sys.stdout.flush()

    try:
        tty.setraw(descripteur)

        while True:
            touche = sys.stdin.read(1)

            if touche in TOUCHE_ENTREE:
                sys.stdout.write("\r\n")
                return "".join(caracteres)

            if touche == TOUCHE_CTRL_C:
                raise KeyboardInterrupt

            if touche == TOUCHE_CTRL_D:
                sys.stdout.write("\r\n")
                return "".join(caracteres)

            if touche in TOUCHES_RETOUR:
                if position > 0:
                    del caracteres[position - 1]
                    position -= 1
                    _rafraichir_ligne(invite, caracteres, position)
                continue

            if touche == TOUCHE_ECHAP:
                position = _traiter_sequence_echap(caracteres, position)
                _rafraichir_ligne(invite, caracteres, position)
                continue

            if touche.isprintable():
                caracteres.insert(position, touche)
                position += 1
                _rafraichir_ligne(invite, caracteres, position)

    finally:
        termios.tcsetattr(descripteur, termios.TCSADRAIN, attributs)


def _traiter_sequence_echap(caracteres: list[str], position: int) -> int:
    """
    Traiter les séquences clavier courantes : flèches, début, fin et suppression.
    """

    sequence = sys.stdin.read(1)

    if sequence != SEQUENCE_CONTROLE:
        return position

    code = sys.stdin.read(1)

    if code == SEQUENCE_GAUCHE:
        return max(position - 1, 0)

    if code == SEQUENCE_DROITE:
        return min(position + 1, len(caracteres))

    if code == SEQUENCE_DEBUT:
        return 0

    if code == SEQUENCE_FIN:
        return len(caracteres)

    if code == TOUCHE_SUPPRESSION and sys.stdin.read(1) == FIN_SEQUENCE:
        if position < len(caracteres):
            del caracteres[position]
        return position

    return position


def _rafraichir_ligne(invite: str, caracteres: list[str], position: int) -> None:
    """
    Réafficher la ligne complète et replacer le curseur.
    """

    recul = len(caracteres) - position
    sys.stdout.write("\r" + invite + "".join(caracteres) + "\x1b[0K")

    if recul > 0:
        sys.stdout.write(f"\x1b[{recul}D")

    sys.stdout.flush()
