"""
Enregistrer un dataset pilote LeRobot avec un SO-101 follower, un SO-101 leader
et une caméra globale Arducam.

Objectif :
Enregistrer 10 épisodes simples où le robot prend un cube noir et le dépose
dans un carré beige de 10 x 10 cm.

Contrôles pendant l'enregistrement :
- Flèche droite : terminer l'épisode courant et passer au suivant.
- Flèche gauche : annuler l'épisode courant et le recommencer.
- Échap : arrêter la session.
"""

import subprocess

from lerobot.cameras.opencv import OpenCVCameraConfig
from lerobot.common.control_utils import init_keyboard_listener
from lerobot.datasets import LeRobotDataset
from lerobot.processor import make_default_processors
from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig
from lerobot.scripts.lerobot_record import record_loop
from lerobot.teleoperators.so_leader import SO101Leader, SO101LeaderConfig
from lerobot.utils.feature_utils import hw_to_dataset_features


PORT_LEADER = "/dev/ttyACM0"
PORT_FOLLOWER = "/dev/ttyACM1"

ID_LEADER = "bras_leader"
ID_FOLLOWER = "bras_suiveur"

CAMERA_ARDUCAM = "/dev/video2"

FPS = 30
LARGEUR_IMAGE = 1280
HAUTEUR_IMAGE = 720

NB_EPISODES = 10
DUREE_EPISODE_S = 20
DUREE_REINITIALISATION_S = 10

REPO_DATASET = "taubore/so101_cube_vers_carre_pilote"
TACHE = "Prendre le cube noir et le déposer dans le carré beige."


def regler_camera_60_hz() -> None:
    """
    Régler la fréquence anti-scintillement de la caméra pour le Québec.

    La valeur 2 correspond normalement à 60 Hz avec les caméras UVC/V4L2.
    Cette commande évite de dépendre d'un réglage manuel fait avant le script.
    """

    subprocess.run(
        [
            "v4l2-ctl",
            "-d",
            CAMERA_ARDUCAM,
            "--set-ctrl",
            "power_line_frequency=2",
        ],
        check=False,
    )


def creer_robot() -> SO101Follower:
    """
    Créer le bras suiveur avec la caméra globale.
    """

    cameras = {
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

    action_features = hw_to_dataset_features(robot.action_features, "action")
    observation_features = hw_to_dataset_features(robot.observation_features, "observation")
    dataset_features = {**action_features, **observation_features}

    return LeRobotDataset.create(
        repo_id=REPO_DATASET,
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

    regler_camera_60_hz()

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

        while episode < NB_EPISODES and not events["stop_recording"]:
            print(f"Épisode {episode + 1}/{NB_EPISODES}")

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

            if events["rerecord_episode"]:
                events["rerecord_episode"] = False
                events["exit_early"] = False
                dataset.clear_episode_buffer()
                continue

            dataset.save_episode()
            episode += 1

            if episode < NB_EPISODES and not events["stop_recording"]:
                print("Réinitialisation")

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
        teleop.disconnect()
        robot.disconnect()

    print("Terminé")


if __name__ == "__main__":
    enregistrer_dataset()