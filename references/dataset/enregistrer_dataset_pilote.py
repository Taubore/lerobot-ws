"""
Enregistrer un dataset pilote LeRobot avec un SO-101 follower, un SO-101 leader
et une caméra globale Arducam.

Objectif :
Enregistrer 10 épisodes simples où le robot prend un cube noir et le dépose
dans un carré beige de 10 x 10 cm.

Contrôles pendant l'enregistrement :
- Flèche droite : terminer l'épisode courant et passer au suivant.
- Flèche gauche : annuler l'épisode courant, réinitialiser, puis le recommencer.
- Échap : arrêter la session.
"""

from pathlib import Path
from typing import Any

from lerobot.cameras import CameraConfig
from lerobot.cameras.opencv import OpenCVCameraConfig
from lerobot.common.control_utils import init_keyboard_listener
from lerobot.datasets import LeRobotDataset
from lerobot.processor import make_default_processors
from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig
from lerobot.scripts.lerobot_record import record_loop
from lerobot.teleoperators.so_leader import SO101Leader, SO101LeaderConfig
from lerobot.utils.feature_utils import hw_to_dataset_features
from lerobot.datasets.video_utils import VideoEncodingManager

from commun import camera_v4l2
from commun import utilitaires

PORT_LEADER = "/dev/ttyACM0"
PORT_FOLLOWER = "/dev/ttyACM1"

ID_LEADER = "bras_leader"
ID_FOLLOWER = "bras_suiveur"

CAMERA_ARDUCAM = Path("/dev/video2")

FPS = 30
LARGEUR_IMAGE = 1280
HAUTEUR_IMAGE = 720

NB_EPISODES = 10
DUREE_EPISODE_S = 25
DUREE_REINITIALISATION_S = 3

EMPLACEMENT_PROJET = Path("/home/taubore/Projets/lerobot/lerobot-ws")
EMPLACEMENT_DATASETS = EMPLACEMENT_PROJET / "datasets"

REPO_DATASET = "taubore/deplacer_cube_v01"
TACHE = "Prendre le cube noir et le déposer dans le carré beige."


def creer_robot() -> SO101Follower:
    """
    Créer le bras suiveur avec la caméra globale.
    """

    cameras: dict[str, CameraConfig] = {
        "globale": OpenCVCameraConfig(
            index_or_path=CAMERA_ARDUCAM,
            width=LARGEUR_IMAGE,
            height=HAUTEUR_IMAGE,
            fps=FPS,
            fourcc="MJPG",
        )
    }

    config = SO101FollowerConfig(
        port=PORT_FOLLOWER,
        id=ID_FOLLOWER,
        cameras=cameras,
    )

    return SO101Follower(config)


def creer_teleop() -> SO101Leader:
    """
    Créer le bras leader utilisé pour la téléopération.
    """

    config = SO101LeaderConfig(
        port=PORT_LEADER,
        id=ID_LEADER,
    )

    return SO101Leader(config)


def creer_dataset(robot: SO101Follower) -> LeRobotDataset:
    """
    Créer le dataset LeRobot à partir des capacités réelles du robot.

    Les caractéristiques du dataset sont dérivées du robot pour éviter de
    déclarer manuellement les noms des moteurs, actions, états et images.
    """

    action_hw_features: dict[str, type | tuple[Any, ...]] = dict(robot.action_features)
    observation_hw_features: dict[str, type | tuple[Any, ...]] = dict(robot.observation_features)

    action_features = hw_to_dataset_features(action_hw_features, "action")
    observation_features = hw_to_dataset_features(observation_hw_features, "observation")
    dataset_features = {**action_features, **observation_features}

    return LeRobotDataset.create(
        repo_id=REPO_DATASET,
        root=EMPLACEMENT_DATASETS / REPO_DATASET,
        fps=FPS,
        features=dataset_features,
        robot_type=robot.name,
        use_videos=True,
        image_writer_threads=4,
    )


def enregistrer_dataset() -> None:
    """
    Enregistrer les épisodes du dataset pilote.
    """

    camera_v4l2.initialiser_camera_arducam(str(CAMERA_ARDUCAM))

    robot = creer_robot()
    teleop = creer_teleop()
    dataset = None

    try:
        robot.connect()
        teleop.connect()

        dataset = creer_dataset(robot)

        _, events = init_keyboard_listener()

        (
            teleop_action_processor,
            robot_action_processor,
            robot_observation_processor,
        ) = make_default_processors()

        episode = 0

        with VideoEncodingManager(dataset):
            while episode < NB_EPISODES and not events["stop_recording"]:
                print(f"Épisode {episode + 1}/{NB_EPISODES}")
                utilitaires.jouer_debut_episode()

                record_loop(
                    robot=robot,
                    events=events,
                    fps=FPS,
                    teleop_action_processor=teleop_action_processor,
                    robot_action_processor=robot_action_processor,
                    robot_observation_processor=robot_observation_processor,
                    teleop=teleop,
                    dataset=dataset,
                    control_time_s=DUREE_EPISODE_S,
                    single_task=TACHE,
                    display_data=False,
                )

                utilitaires.jouer_fin_episode()

                if events["rerecord_episode"]:
                    events["rerecord_episode"] = False
                    events["exit_early"] = False
                    dataset.clear_episode_buffer()

                    if not events["stop_recording"]:
                        print("Réinitialisation avant reprise")
                        utilitaires.jouer_bip_reinitialisation()

                        record_loop(
                            robot=robot,
                            events=events,
                            fps=FPS,
                            teleop_action_processor=teleop_action_processor,
                            robot_action_processor=robot_action_processor,
                            robot_observation_processor=robot_observation_processor,
                            teleop=teleop,
                            control_time_s=DUREE_REINITIALISATION_S,
                            single_task=TACHE,
                            display_data=False,
                        )

                    continue

                dataset.save_episode()
                episode += 1

                if episode < NB_EPISODES and not events["stop_recording"]:
                    print("Réinitialisation")
                    utilitaires.jouer_bip_reinitialisation()

                    record_loop(
                        robot=robot,
                        events=events,
                        fps=FPS,
                        teleop_action_processor=teleop_action_processor,
                        robot_action_processor=robot_action_processor,
                        robot_observation_processor=robot_observation_processor,
                        teleop=teleop,
                        control_time_s=DUREE_REINITIALISATION_S,
                        single_task=TACHE,
                        display_data=False,
                    )

    except KeyboardInterrupt:
        pass

    finally:
        if dataset is not None:
            dataset.finalize()

        if teleop.is_connected:
            teleop.disconnect()

        if robot.is_connected:
            robot.disconnect()        

    print("Terminé")
    utilitaires.jouer_bips_fin_cycle()


if __name__ == "__main__":
    enregistrer_dataset()
