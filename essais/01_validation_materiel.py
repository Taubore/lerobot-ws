"""
Valide rapidement l'environnement matériel de base pour LeRobot.

Objectif :
- confirmer que VSCode utilise le bon environnement Python ;
- confirmer que LeRobot officiel est importable ;
- vérifier la présence des ports USB des bras ;
- ouvrir l'Arducam en OpenCV ;
- afficher une image caméra en 1280 x 720.

Ce script ne bouge aucun moteur.
"""

from pathlib import Path
import sys
import time

import cv2


PORT_LEADER = "/dev/ttyACM0"
PORT_FOLLOWER = "/dev/ttyACM1"

CAMERA_ARDUCAM = "/dev/video2"
LARGEUR_CAMERA = 1280
HAUTEUR_CAMERA = 720
FPS_CAMERA = 30


def afficher_titre(titre: str) -> None:
    """
    Affiche un titre de section lisible dans la console.
    """
    print()
    print("=" * 70)
    print(titre)
    print("=" * 70)


def verifier_python() -> None:
    """
    Affiche l'exécutable Python actif.

    Cela permet de confirmer que VSCode utilise bien l'environnement conda
    prévu pour LeRobot.
    """
    afficher_titre("Python actif")

    print(f"Exécutable : {sys.executable}")
    print(f"Version    : {sys.version}")


def verifier_import_lerobot() -> None:
    """
    Vérifie que le module LeRobot est importable.
    """
    afficher_titre("Import de LeRobot")

    try:
        import lerobot

        print("Résultat   : OK")
        print(f"Emplacement : {lerobot.__file__}")

    except ImportError as erreur:
        print("Résultat   : ÉCHEC")
        print(erreur)
        raise


def verifier_ports_usb() -> None:
    """
    Vérifie que les ports USB attendus existent.

    On ne tente pas encore de communiquer avec les moteurs. Cette étape valide
    seulement que Linux expose bien les périphériques attendus.
    """
    afficher_titre("Ports USB des bras")

    ports = {
        "leader": Path(PORT_LEADER),
        "follower": Path(PORT_FOLLOWER),
    }

    for nom, chemin in ports.items():
        if chemin.exists():
            print(f"{nom:8} : OK     {chemin}")
        else:
            print(f"{nom:8} : ABSENT {chemin}")


def configurer_camera(capture: cv2.VideoCapture) -> None:
    """
    Configure la caméra en MJPG 1280 x 720 à 30 FPS.

    MJPG est important ici, car l'Arducam offre de meilleures cadences dans ce
    format qu'en YUYV à haute résolution.
    """
    codec_mjpg = cv2.VideoWriter.fourcc(*"MJPG")

    capture.set(cv2.CAP_PROP_FOURCC, codec_mjpg)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, LARGEUR_CAMERA)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, HAUTEUR_CAMERA)
    capture.set(cv2.CAP_PROP_FPS, FPS_CAMERA)


def afficher_infos_camera(capture: cv2.VideoCapture) -> None:
    """
    Affiche les paramètres réellement obtenus après configuration.

    OpenCV peut accepter une demande sans garantir que la caméra appliquera
    exactement tous les paramètres.
    """
    largeur = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    hauteur = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = capture.get(cv2.CAP_PROP_FPS)
    fourcc = int(capture.get(cv2.CAP_PROP_FOURCC))

    codec = "".join(chr((fourcc >> 8 * i) & 0xFF) for i in range(4))

    print(f"Résolution demandée : {LARGEUR_CAMERA} x {HAUTEUR_CAMERA}")
    print(f"Résolution obtenue  : {largeur} x {hauteur}")
    print(f"FPS obtenus         : {fps:.1f}")
    print(f"Codec obtenu        : {codec}")


def tester_camera() -> None:
    """
    Ouvre l'Arducam et enregistre une image de validation.

    On évite `cv2.imshow()`, car certains paquets OpenCV installés par `pip`
    ou `conda` n'incluent pas le support graphique GTK nécessaire sous Linux.
    """
    afficher_titre("Caméra Arducam")

    capture = cv2.VideoCapture(CAMERA_ARDUCAM, cv2.CAP_V4L2)

    if not capture.isOpened():
        raise RuntimeError(f"Impossible d'ouvrir la caméra : {CAMERA_ARDUCAM}")

    try:
        configurer_camera(capture)
        time.sleep(0.5)

        afficher_infos_camera(capture)

        succes, image = capture.read()

        if not succes:
            raise RuntimeError("Lecture caméra échouée.")

        chemin_image = Path(__file__).parent / "validation_arducam.jpg"
        succes_ecriture = cv2.imwrite(str(chemin_image), image)

        if not succes_ecriture:
            raise RuntimeError(f"Impossible d'écrire l'image : {chemin_image}")

        print()
        print("Capture caméra : OK")
        print(f"Image enregistrée : {chemin_image}")

    finally:
        capture.release()

def main() -> None:
    """
    Exécute la validation matérielle minimale.
    """
    verifier_python()
    verifier_import_lerobot()
    verifier_ports_usb()
    tester_camera()

    afficher_titre("Résultat")
    print("Validation terminée.")


if __name__ == "__main__":
    main()