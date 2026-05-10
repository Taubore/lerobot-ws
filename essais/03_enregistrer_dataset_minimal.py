"""
Enregistre un premier mini-dataset LeRobot avec le SO-101.

Objectif :
- connecter le bras follower ;
- connecter le bras leader ;
- utiliser l'Arducam comme caméra globale ;
- enregistrer quelques épisodes courts ;
- sauvegarder un dataset LeRobot local ;
- ne rien pousser sur Hugging Face Hub pour ce premier essai.

Ce script utilise l'API Python de LeRobot, pas la commande `lerobot-record`.
"""

from pathlib import Path

from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.configs.dataset import DatasetRecordConfig
from lerobot.robots.so_follower.config_so_follower import SO101FollowerConfig
from lerobot.scripts.lerobot_record import RecordConfig, record
from lerobot.teleoperators.so_leader.config_so_leader import SO101LeaderConfig

from camera_v4l2 import initialiser_camera_arducam

PORT_LEADER = "/dev/ttyACM0"
PORT_FOLLOWER = "/dev/ttyACM1"

ID_LEADER = "bras_leader"
ID_FOLLOWER = "bras_suiveur"

CAMERA_ARDUCAM = "/dev/video2"

FPS = 30
LARGEUR_IMAGE = 1280
HAUTEUR_IMAGE = 720

NB_EPISODES = 2
DUREE_EPISODE_S = 15
DUREE_RESET_S = 8

TACHE = "Déplacer un petit objet vers une zone cible"

RACINE_DATASETS = Path("/home/taubore/Projets/lerobot/lerobot-ws/datasets")
REPO_ID_DATASET = "Taubore/so101_premier_dataset_local"


def creer_config_camera() -> OpenCVCameraConfig:
    """
    Crée la configuration de l'Arducam utilisée comme caméra globale.

    La caméra est volontairement configurée en 1280x720 à 30 FPS pour commencer.
    C'est un bon compromis entre qualité d'image, charge CPU et stabilité.
    """
    return OpenCVCameraConfig(
        index_or_path=Path(CAMERA_ARDUCAM),
        width=LARGEUR_IMAGE,
        height=HAUTEUR_IMAGE,
        fps=FPS,
    )


def creer_config_robot() -> SO101FollowerConfig:
    """
    Crée la configuration du bras follower avec la caméra globale.

    Le robot est responsable des observations :
    - positions moteurs ;
    - images caméra ;
    - autres états exposés par LeRobot.
    """
    return SO101FollowerConfig(
        id=ID_FOLLOWER,
        port=PORT_FOLLOWER,
        max_relative_target=30.0,
        cameras={
            "front": creer_config_camera(),
        },
    )


def creer_config_teleoperation() -> SO101LeaderConfig:
    """
    Crée la configuration du bras leader.

    Le leader fournit les actions humaines qui seront enregistrées dans le dataset.
    """
    return SO101LeaderConfig(
        id=ID_LEADER,
        port=PORT_LEADER,
    )


def creer_config_dataset() -> DatasetRecordConfig:
    """
    Crée la configuration du mini-dataset local.

    `push_to_hub=False` évite tout envoi externe. Le but est seulement de valider
    la collecte locale avant de produire un dataset plus sérieux.
    """
    return DatasetRecordConfig(
        repo_id=REPO_ID_DATASET,
        root=RACINE_DATASETS,
        fps=FPS,
        num_episodes=NB_EPISODES,
        episode_time_s=DUREE_EPISODE_S,
        reset_time_s=DUREE_RESET_S,
        single_task=TACHE,
        push_to_hub=False,
        video=True,
        streaming_encoding=True,
        encoder_threads=2,
        vcodec="auto",
    )


def main() -> None:
    """
    Enregistre le mini-dataset.

    Pendant chaque épisode :
    - déplacer doucement le leader ;
    - garder l'objet visible ;
    - éviter les gestes brusques ;
    - viser une démonstration claire plutôt qu'une performance rapide.
    """

    initialiser_camera_arducam(CAMERA_ARDUCAM)

    RACINE_DATASETS.mkdir(parents=True, exist_ok=True)

    config = RecordConfig(
        robot=creer_config_robot(),
        teleop=creer_config_teleoperation(),
        dataset=creer_config_dataset(),
        display_data=True,
        play_sounds=False,
        resume=False,
    )

    dataset = record(config)

    print()
    print("=" * 70)
    print("Dataset enregistré")
    print("=" * 70)
    print(f"Épisodes enregistrés : {dataset.num_episodes}")
    print(f"Dossier racine       : {RACINE_DATASETS}")
    print(f"Repo ID dataset      : {dataset.repo_id}")
    print()
    print("Prochaine validation : ouvrir le dossier du dataset et vérifier :")
    print("- meta/")
    print("- data/")
    print("- videos/")


if __name__ == "__main__":
    main()