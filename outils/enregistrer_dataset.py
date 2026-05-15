"""
Enregistrer un lot brut de dataset LeRobot avec le fonctionnement local par défaut.

Objectif :
Créer des lots d'enregistrement jetables ou validables dans le cache LeRobot, sans remplir le
workspace avec des essais ratés. Les datasets officialisés pourront ensuite être copiés ou
fusionnés dans le dossier `datasets/` du projet.

Stockage :
- Lot brut : `~/.cache/huggingface/lerobot/{repo_id}`.
- Dataset officialisé : `datasets/` dans le workspace, hors de ce script.

Contrôles pendant l'enregistrement :
- Flèche droite : terminer/accepter l'épisode courant ou passer à l'étape suivante.
- Flèche gauche : annuler l'épisode courant, réinitialiser, puis le recommencer.
- Échap : arrêter la session, encoder les vidéos et terminer proprement.
"""

import shutil
from pathlib import Path
from time import sleep

from lerobot.cameras import CameraConfig
from lerobot.cameras.opencv import OpenCVCameraConfig
from lerobot.common.control_utils import init_keyboard_listener
from lerobot.datasets import (
    LeRobotDataset,
    VideoEncodingManager,
    aggregate_pipeline_dataset_features,
    create_initial_features,
)
from lerobot.processor import make_default_processors
from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig
from lerobot.scripts.lerobot_record import record_loop
from lerobot.teleoperators.so_leader import SO101Leader, SO101LeaderConfig
from lerobot.utils.constants import HF_LEROBOT_HOME
from lerobot.utils.feature_utils import combine_feature_dicts

from commun import camera_v4l2
from commun import config_lerobot
from commun import utils
from commun import utils_lerobot

REPONSE_SUPPRIMER_DATASET = "o"


def creer_robot(config_ws: config_lerobot.ConfigLeRobotWs) -> SO101Follower:
    """
    Créer le bras suiveur avec la caméra globale.
    """

    camera_globale = config_ws.materiel.camera_globale

    cameras: dict[str, CameraConfig] = {
        camera_globale.nom: OpenCVCameraConfig(
            index_or_path=camera_globale.chemin,
            width=camera_globale.largeur,
            height=camera_globale.hauteur,
            fps=camera_globale.fps,
            fourcc=camera_globale.fourcc,
        )
    }

    config_robot = SO101FollowerConfig(
        port=config_ws.materiel.robot.port_follower,
        id=config_ws.materiel.robot.id_follower,
        cameras=cameras,
    )

    return SO101Follower(config_robot)


def creer_teleop(config_ws: config_lerobot.ConfigLeRobotWs) -> SO101Leader:
    """
    Créer le bras leader utilisé pour la téléopération.
    """

    config_teleop = SO101LeaderConfig(
        port=config_ws.materiel.robot.port_leader,
        id=config_ws.materiel.robot.id_leader,
    )

    return SO101Leader(config_teleop)


def creer_dataset(
    robot: SO101Follower,
    repo_id: str,
    config_dataset: config_lerobot.ConfigDatasetEnregistrement,
    fps: int,
) -> LeRobotDataset:
    """
    Créer le dataset en laissant LeRobot choisir son emplacement local par défaut.

    `root` n'est pas transmis volontairement : LeRobot écrit donc dans
    `~/.cache/huggingface/lerobot/{repo_id}`. Le script n'appelle jamais `push_to_hub()`, ce qui
    correspond au comportement souhaité de `--dataset.push_to_hub=False`.
    """

    (
        teleop_action_processor,
        _robot_action_processor,
        robot_observation_processor,
    ) = make_default_processors()

    action_features = aggregate_pipeline_dataset_features(
        pipeline=teleop_action_processor,
        initial_features=create_initial_features(action=robot.action_features),
        use_videos=config_dataset.use_videos,
    )
    observation_features = aggregate_pipeline_dataset_features(
        pipeline=robot_observation_processor,
        initial_features=create_initial_features(observation=robot.observation_features),
        use_videos=config_dataset.use_videos,
    )
    dataset_features = combine_feature_dicts(action_features, observation_features)

    return LeRobotDataset.create(
        repo_id=repo_id,
        fps=fps,
        features=dataset_features,
        robot_type=robot.name,
        use_videos=config_dataset.use_videos,
        image_writer_threads=config_dataset.image_writer_threads,
    )


def chemin_dataset_cache(repo_id: str) -> Path:
    """
    Retourner l'emplacement local par défaut du dataset LeRobot.
    """

    return HF_LEROBOT_HOME / repo_id


def supprimer_dataset_cache(repo_id: str) -> None:
    """
    Supprimer un dataset brut existant dans le cache LeRobot.
    """

    emplacement_lerobot = HF_LEROBOT_HOME.resolve()
    chemin_dataset = chemin_dataset_cache(repo_id).resolve()
    chemin_dataset.relative_to(emplacement_lerobot)

    shutil.rmtree(chemin_dataset)
    print("Suppression du dataset brut effectuée.")


def attendre_demarrage(delai_avant_demarrage_s: int) -> None:
    """
    Afficher le compte à rebours avant le début de l'enregistrement.
    """

    utils_lerobot.jouer_son_reinitialisation()

    for secondes_restantes in range(delai_avant_demarrage_s, 0, -1):
        print(f"Démarrage dans {secondes_restantes} s   ", end="\r", flush=True)
        sleep(1)

    print("Démarrage maintenant.        ")
    utils_lerobot.jouer_son_debut_episode()


def enregistrer_dataset() -> None:
    """
    Enregistrer les épisodes d'un lot brut dans le cache LeRobot.
    """

    config = config_lerobot.charger_config()
    camera_globale = config.materiel.camera_globale
    config_dataset = config.enregistrement.dataset

    if config_dataset.push_to_hub:
        raise ValueError("Ce script d'enregistrement brut doit garder `push_to_hub = false`.")

    camera_v4l2.initialiser_camera_arducam(
        camera=str(camera_globale.chemin),
        largeur=camera_globale.largeur,
        hauteur=camera_globale.hauteur,
        fps=camera_globale.fps,
    )

    robot = creer_robot(config)
    teleop = creer_teleop(config)
    dataset = None
    listener = None

    try:
        robot.connect()
        teleop.connect()
        listener, events = init_keyboard_listener()

        print("Enregistrement d'un lot brut LeRobot")
        print(f"Upload Hub : {config_dataset.push_to_hub}")
        print("Contrôles LeRobot :")
        print("- Flèche droite : accepter l'épisode ou passer à l'étape suivante.")
        print("- Flèche gauche : annuler et recommencer l'épisode courant.")
        print("- Échap : arrêter, encoder les vidéos et terminer proprement.")
        print()

        repo_dataset = utils.saisir_avec_texte_defaut(
            "Nom du dataset : ",
            config_dataset.repo_id_defaut,
        )
        tache = utils.saisir_avec_texte_defaut("Tâche unique : ", config_dataset.tache_defaut)
        print()
        print(f"Stockage prévu : {chemin_dataset_cache(repo_dataset)}")
        print("Utiliser la même tâche unique pour tous les lots validés de cette tâche.")
        print()

        try:
            dataset = creer_dataset(robot, repo_dataset, config_dataset, camera_globale.fps)

        except FileExistsError:
            message = "Le lot existe déjà dans le cache. Le supprimer et poursuivre ? [o/N] : "
            reponse = input(message)

            if reponse.strip().lower() != REPONSE_SUPPRIMER_DATASET:
                return

            supprimer_dataset_cache(repo_dataset)
            dataset = creer_dataset(robot, repo_dataset, config_dataset, camera_globale.fps)

        (
            teleop_action_processor,
            robot_action_processor,
            robot_observation_processor,
        ) = make_default_processors()

        attendre_demarrage(config.enregistrement.delai_avant_demarrage_s)

        episode = 0

        with VideoEncodingManager(dataset):
            while episode < config_dataset.nb_episodes and not events["stop_recording"]:
                print(f"----- Épisode {episode + 1}/{config_dataset.nb_episodes} -----")
                utils_lerobot.jouer_son_debut_episode()

                record_loop(
                    robot=robot,
                    events=events,
                    fps=camera_globale.fps,
                    teleop_action_processor=teleop_action_processor,
                    robot_action_processor=robot_action_processor,
                    robot_observation_processor=robot_observation_processor,
                    teleop=teleop,
                    dataset=dataset,
                    control_time_s=int(config_dataset.duree_episode_s),
                    single_task=tache,
                    display_data=False,
                )

                if events["rerecord_episode"]:
                    events["rerecord_episode"] = False
                    events["exit_early"] = False
                    dataset.clear_episode_buffer()
                    print("Épisode annulé. Réinitialisation avant reprise.")
                    utils_lerobot.jouer_son_annulation_episode()

                    if not events["stop_recording"]:
                        record_loop(
                            robot=robot,
                            events=events,
                            fps=camera_globale.fps,
                            teleop_action_processor=teleop_action_processor,
                            robot_action_processor=robot_action_processor,
                            robot_observation_processor=robot_observation_processor,
                            teleop=teleop,
                            control_time_s=int(config_dataset.duree_reinitialisation_s),
                            single_task=tache,
                            display_data=False,
                        )
                    
                    continue

                dataset.save_episode()
                episode += 1
                print(f"Épisode sauvegardé : {episode}/{config_dataset.nb_episodes}")
                utils_lerobot.jouer_son_fin_episode()

                if episode < config_dataset.nb_episodes and not events["stop_recording"]:
                    print("Réinitialisation")
                    utils_lerobot.jouer_son_reinitialisation()

                    record_loop(
                        robot=robot,
                        events=events,
                        fps=camera_globale.fps,
                        teleop_action_processor=teleop_action_processor,
                        robot_action_processor=robot_action_processor,
                        robot_observation_processor=robot_observation_processor,
                        teleop=teleop,
                        control_time_s=int(config_dataset.duree_reinitialisation_s),
                        single_task=tache,
                        display_data=False,
                    )

    except KeyboardInterrupt:
        print("Interruption clavier.")

    finally:
        if dataset is not None:
            dataset.finalize()

        if teleop.is_connected:
            teleop.disconnect()

        if robot.is_connected:
            robot.disconnect()

        if listener is not None:
            listener.stop()

    print("Terminé.")
    utils_lerobot.jouer_son_fin_entrainement()


if __name__ == "__main__":
    enregistrer_dataset()
