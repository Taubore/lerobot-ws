"""
Fonctions communes pour configurer les caméras USB avec V4L2.

Ces réglages doivent être appliqués avant l'ouverture de la caméra par OpenCV
ou par LeRobot, sinon la caméra peut déjà être utilisée par le processus.
"""

import subprocess
from pathlib import Path


def _appliquer_controle_v4l2(camera: str, controle: str, valeur: int | str) -> None:
    """
    Applique un contrôle V4L2 générique sur une caméra.

    Cette fonction est volontairement bas niveau. Elle ne connaît pas le sens
    métier du réglage ; elle exécute seulement la configuration demandée.
    """
    chemin_camera = Path(camera)

    if not chemin_camera.exists():
        raise FileNotFoundError(f"Caméra introuvable : {camera}")

    commande = [
        "v4l2-ctl",
        "-d",
        camera,
        f"--set-ctrl={controle}={valeur}",
    ]

    try:
        subprocess.run(
            commande,
            check=True,
            text=True,
            capture_output=True,
        )

    except FileNotFoundError as erreur:
        raise RuntimeError(
            "La commande `v4l2-ctl` est introuvable. "
            "Installe le paquet `v4l-utils`."
        ) from erreur

    except subprocess.CalledProcessError as erreur:
        message = erreur.stderr.strip() or erreur.stdout.strip()

        raise RuntimeError(
            f"Impossible d'appliquer le contrôle `{controle}` sur {camera}.\n"
            f"Valeur demandée : {valeur}\n"
            f"Détail : {message}"
        ) from erreur


def initialiser_camera_arducam(camera: str) -> None:
    """
    Initialise l'Arducam pour les scripts LeRobot du projet.

    Réglages actuels :
    - `power_line_frequency=2` : anti-scintillement 60 Hz.

    Cette fonction est le point d'entrée à utiliser dans les scripts.
    On pourra y ajouter plus tard d'autres réglages V4L2 sans modifier tous les
    scripts d'essai.
    """
    _appliquer_controle_v4l2(
        camera=camera,
        controle="power_line_frequency",
        valeur=2,
    )