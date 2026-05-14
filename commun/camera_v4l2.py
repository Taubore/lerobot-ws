"""
Fonctions communes pour configurer les caméras USB avec l'utilitaire V4L2.

Ces réglages doivent être appliqués avant l'ouverture de la caméra par OpenCV sinon la caméra 
peut déjà être utilisée par le processus.
"""

import subprocess
from pathlib import Path

CODEC_MJPEG = "MJPG"

def _executer_v4l2(commande: list[str], description: str) -> None:
    """
    Exécute une commande V4L2 et reformate les erreurs courantes.
    """
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
            f"Impossible d'appliquer le réglage V4L2 : {description}\n"
            f"Détail : {message}"
        ) from erreur


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

    _executer_v4l2(
        commande=commande,
        description=f"contrôle `{controle}` sur {camera}, valeur demandée `{valeur}`",
    )


def _appliquer_format_video_v4l2(camera: str, largeur: int, hauteur: int, fps: int) -> None:
    """
    Force le format vidéo demandé avant l'ouverture de la caméra par OpenCV.
    """
    chemin_camera = Path(camera)

    if not chemin_camera.exists():
        raise FileNotFoundError(f"Caméra introuvable : {camera}")

    commande = [
        "v4l2-ctl",
        "-d",
        camera,
        f"--set-fmt-video=width={largeur},height={hauteur},pixelformat={CODEC_MJPEG}",
        f"--set-parm={fps}",
    ]

    _executer_v4l2(
        commande=commande,
        description=f"format {CODEC_MJPEG} {largeur} x {hauteur} à {fps} FPS sur {camera}",
    )


def initialiser_camera_arducam(camera: str, largeur: int, hauteur: int, fps: int) -> None:
    """
    Initialise l'Arducam.

    Réglages actuels :
    - Format vidéo MJPG avec la résolution et le FPS demandés.
    - `power_line_frequency=2` : anti-scintillement 60 Hz (50 Hz par défaut)
    - `exposure_dynamic_framerate=0` : ne pas autoriser la cadence selon l’exposition

    Cette fonction est le point d'entrée à utiliser pour initialiser une caméra Arducam.
    """
    _appliquer_format_video_v4l2(
        camera=camera,
        largeur=largeur,
        hauteur=hauteur,
        fps=fps,
    )

    _appliquer_controle_v4l2(
        camera=camera,
        controle="power_line_frequency",
        valeur=2,
    )

    _appliquer_controle_v4l2(
        camera=camera,
        controle="exposure_dynamic_framerate",
        valeur=0,
    )
