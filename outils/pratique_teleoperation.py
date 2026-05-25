"""
Pratiquer la téléopération d'un bras LeRobot follower SO-101 avec un leader SO-101.

Le script ouvre Rerun au démarrage, connecte la caméra globale du follower, puis affiche les
observations caméra pendant toute la session de pratique. La lecture de la caméra s'arrête à la
déconnexion du robot, dans le bloc `finally`.

Hypothèses importantes :
- le bras leader est connecté et opérationnel ;
- le bras follower est connecté et opérationnel ;
- la caméra globale configurée dans `config_lerobot_ws.toml` est disponible.
"""

from pathlib import Path
from time import perf_counter

from lerobot.cameras import CameraConfig
from lerobot.cameras.opencv import OpenCVCameraConfig
from lerobot.processor import make_default_processors
from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig
from lerobot.scripts.lerobot_record import init_rerun, log_rerun_data
from lerobot.teleoperators.so_leader import SO101Leader, SO101LeaderConfig
from lerobot.utils.robot_utils import precise_sleep

from commun import camera_v4l2
from commun import config_lerobot

CHEMIN_CONFIG = Path(__file__).resolve().parent / "config_lerobot_ws.toml"
NOM_SESSION_RERUN = "pratique_teleoperation"


def creer_robot(config: config_lerobot.ConfigLeRobotWs) -> SO101Follower:
    """
    Créer le bras SO-101 follower avec la caméra globale.
    """

    robot = config.materiel.robot
    camera = config.materiel.camera_globale
    cameras: dict[str, CameraConfig] = {
        camera.nom: OpenCVCameraConfig(
            index_or_path=camera.chemin,
            width=camera.largeur,
            height=camera.hauteur,
            fps=camera.fps,
            fourcc=camera.fourcc,
        )
    }

    config_robot = SO101FollowerConfig(
        port=robot.port_follower,
        id=robot.id_follower,
        cameras=cameras,
    )

    return SO101Follower(config_robot)


def creer_teleop(config: config_lerobot.ConfigLeRobotWs) -> SO101Leader:
    """
    Créer le bras SO-101 leader utilisé pour la téléopération.
    """

    robot = config.materiel.robot
    config_teleop = SO101LeaderConfig(
        port=robot.port_leader,
        id=robot.id_leader,
    )

    return SO101Leader(config_teleop)


def afficher_demarrage(config: config_lerobot.ConfigLeRobotWs) -> None:
    """
    Afficher les informations utiles avant la pratique.
    """

    camera = config.materiel.camera_globale

    print("Pratique de téléopération SO-101")
    print(f"Session Rerun : {NOM_SESSION_RERUN}")
    print(f"Caméra : {camera.chemin} ({camera.largeur} x {camera.hauteur} à {camera.fps} FPS)")
    print("Contrôle : bouger le bras leader pour piloter le follower.")
    print("Arrêt : Ctrl+C.")
    print()


def pratiquer_teleoperation() -> None:
    """
    Démarrer la téléopération avec visualisation caméra dans Rerun.
    """

    config = config_lerobot.charger_config(CHEMIN_CONFIG)
    camera = config.materiel.camera_globale

    init_rerun(session_name=NOM_SESSION_RERUN)
    afficher_demarrage(config)

    camera_v4l2.initialiser_camera_arducam(
        camera=str(camera.chemin),
        largeur=camera.largeur,
        hauteur=camera.hauteur,
        fps=camera.fps,
    )

    robot = creer_robot(config)
    teleop = creer_teleop(config)
    intervalle_controle_s = 1.0 / camera.fps

    (
        teleop_action_processor,
        robot_action_processor,
        robot_observation_processor,
    ) = make_default_processors()

    try:
        robot.connect()
        teleop.connect()

        while True:
            debut_boucle_s = perf_counter()

            observation = robot.get_observation()
            observation_traitee = robot_observation_processor(observation)

            action = teleop.get_action()
            action_teleop = teleop_action_processor((action, observation))
            action_robot = robot_action_processor((action_teleop, observation))

            robot.send_action(action_robot)
            log_rerun_data(observation=observation_traitee, action=action_teleop)

            duree_boucle_s = perf_counter() - debut_boucle_s
            precise_sleep(max(intervalle_controle_s - duree_boucle_s, 0.0))

    except KeyboardInterrupt:
        print("Interruption clavier.")

    finally:
        if teleop.is_connected:
            teleop.disconnect()

        if robot.is_connected:
            robot.disconnect()


if __name__ == "__main__":
    pratiquer_teleoperation()
