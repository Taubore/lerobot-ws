"""
Enregistrer un lot brut local de dataset LeRobot.

Ce script crée un lot dans le cache LeRobot :
`~/.cache/huggingface/lerobot/{repo_id}`.

Les étapes d'inspection, d'officialisation, de fusion et d'entraînement sont volontairement
laissées à d'autres scripts.
"""

import shutil
import sys
import termios
from pathlib import Path
from time import sleep
from typing import Any

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

CHOIX_ANNULER = "1"
CHOIX_SUPPRIMER = "2"
CHOIX_NOUVEAU_NOM = "3"
DELAI_APRES_ANNULATION_S = 1.0


def desactiver_echo_terminal() -> list[Any] | None:
    """
    Empêcher le terminal d'afficher les séquences des touches de contrôle.
    """

    if not sys.stdin.isatty():
        return None

    descripteur = sys.stdin.fileno()
    attributs = termios.tcgetattr(descripteur)
    nouveaux_attributs = attributs.copy()
    nouveaux_attributs[3] = nouveaux_attributs[3] & ~termios.ECHO
    termios.tcsetattr(descripteur, termios.TCSADRAIN, nouveaux_attributs)

    return attributs


def restaurer_echo_terminal(attributs: list[Any] | None) -> None:
    """
    Restaurer l'affichage normal des touches saisies dans le terminal.
    """

    if attributs is None:
        return

    termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, attributs)


def saisir_texte(invite: str, texte_defaut: str) -> str:
    """
    Demander un texte non vide avec une valeur par défaut préremplie.
    """

    while True:
        texte = utils.saisir_avec_texte_defaut(invite, texte_defaut).strip()

        if texte:
            return texte

        print("La valeur ne peut pas être vide.")


def creer_robot(config: config_lerobot.ConfigLeRobotWs) -> SO101Follower:
    """
    Créer le bras SO101 follower avec la caméra globale.
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
    Créer le bras SO101 leader utilisé pour la téléopération.
    """

    robot = config.materiel.robot
    config_teleop = SO101LeaderConfig(
        port=robot.port_leader,
        id=robot.id_leader,
    )

    return SO101Leader(config_teleop)


def creer_dataset(
    robot: SO101Follower,
    config: config_lerobot.ConfigLeRobotWs,
    repo_id: str,
) -> LeRobotDataset:
    """
    Créer le dataset dans le cache local LeRobot.

    Le paramètre `root` n'est pas transmis : LeRobot écrit donc dans son emplacement local par
    défaut, sous `HF_LEROBOT_HOME`.
    """

    dataset_config = config.enregistrement.dataset
    (
        teleop_action_processor,
        _robot_action_processor,
        robot_observation_processor,
    ) = make_default_processors()

    action_features = aggregate_pipeline_dataset_features(
        pipeline=teleop_action_processor,
        initial_features=create_initial_features(action=robot.action_features),
        use_videos=dataset_config.use_videos,
    )
    observation_features = aggregate_pipeline_dataset_features(
        pipeline=robot_observation_processor,
        initial_features=create_initial_features(observation=robot.observation_features),
        use_videos=dataset_config.use_videos,
    )

    return LeRobotDataset.create(
        repo_id=repo_id,
        fps=config.materiel.camera_globale.fps,
        features=combine_feature_dicts(action_features, observation_features),
        robot_type=robot.name,
        use_videos=dataset_config.use_videos,
        image_writer_threads=dataset_config.image_writer_threads,
    )


def chemin_dataset_cache(repo_id: str) -> Path:
    """
    Retourner le chemin local d'un dataset dans le cache LeRobot.
    """

    return HF_LEROBOT_HOME / repo_id


def supprimer_dataset_cache(repo_id: str) -> None:
    """
    Supprimer un dataset existant après vérification de son emplacement.
    """

    racine_cache = HF_LEROBOT_HOME.resolve()
    chemin_dataset = chemin_dataset_cache(repo_id).resolve()

    try:
        chemin_dataset.relative_to(racine_cache)

    except ValueError as erreur:
        raise ValueError("Refus de supprimer un dossier hors de HF_LEROBOT_HOME.") from erreur

    if chemin_dataset == racine_cache:
        raise ValueError("Refus de supprimer la racine HF_LEROBOT_HOME.")

    shutil.rmtree(chemin_dataset)
    print("Lot existant supprimé.")


def choisir_repo_dataset(config: config_lerobot.ConfigLeRobotWs) -> str | None:
    """
    Choisir un repo_id disponible ou annuler la session.
    """

    repo_id_defaut = config.enregistrement.dataset.repo_id_defaut

    while True:
        repo_id = saisir_texte("Nom du dataset : ", repo_id_defaut)

        if not chemin_dataset_cache(repo_id).exists():
            return repo_id

        print(f"Le lot existe déjà : {chemin_dataset_cache(repo_id)}")
        print("1. Annuler")
        print("2. Supprimer le lot existant et recommencer")
        print("3. Utiliser un nouveau nom de lot")

        choix = input("Votre choix [1/2/3] : ").strip()

        if choix == CHOIX_ANNULER:
            return None

        if choix == CHOIX_SUPPRIMER:
            supprimer_dataset_cache(repo_id)
            return repo_id

        if choix == CHOIX_NOUVEAU_NOM:
            repo_id_defaut = repo_id
            continue

        print("Choix non reconnu.")


def afficher_demarrage(repo_id: str, tache: str) -> None:
    """
    Afficher les informations utiles avant l'enregistrement.
    """

    print()
    print("Enregistrement d'un lot brut LeRobot")
    print(f"Dataset : {repo_id}")
    print(f"Tâche : {tache}")
    print(f"Stockage : {chemin_dataset_cache(repo_id)}")
    print("Contrôles :")
    print("- Flèche droite : accepter l'épisode.")
    print("- Flèche gauche : recommencer l'épisode.")
    print("- Échap : arrêter proprement.")
    print()


def attendre_demarrage(delai_avant_demarrage_s: int) -> None:
    """
    Attendre quelques secondes avant de commencer l'enregistrement.
    """

    for secondes_restantes in range(delai_avant_demarrage_s, 0, -1):
        print(f"Démarrage dans {secondes_restantes} s   ", end="\r", flush=True)
        sleep(1)

    print("Démarrage maintenant.        ")


def enregistrer_dataset() -> None:
    """
    Enregistrer les épisodes d'un lot brut dans le cache LeRobot.
    """

    config = config_lerobot.charger_config()
    dataset_config = config.enregistrement.dataset
    camera = config.materiel.camera_globale

    if dataset_config.push_to_hub:
        raise ValueError("Ce script exige `push_to_hub = false` dans `config/lerobot_ws.toml`.")

    repo_id = choisir_repo_dataset(config)

    if repo_id is None:
        print("Session annulée.")
        return

    tache = saisir_texte("Tâche : ", dataset_config.tache_defaut)
    afficher_demarrage(repo_id, tache)

    camera_v4l2.initialiser_camera_arducam(
        camera=str(camera.chemin),
        largeur=camera.largeur,
        hauteur=camera.hauteur,
        fps=camera.fps,
    )

    robot = creer_robot(config)
    teleop = creer_teleop(config)
    dataset = None
    listener = None
    attributs_terminal = None
    episodes_sauvegardes = 0

    try:
        attributs_terminal = desactiver_echo_terminal()
        robot.connect()
        teleop.connect()
        listener, events = init_keyboard_listener()
        dataset = creer_dataset(robot, config, repo_id)

        (
            teleop_action_processor,
            robot_action_processor,
            robot_observation_processor,
        ) = make_default_processors()

        attendre_demarrage(config.enregistrement.delai_avant_demarrage_s)

        with VideoEncodingManager(dataset):
            while (
                episodes_sauvegardes < dataset_config.nb_episodes
                and not events["stop_recording"]
            ):
                print(f"Épisode {episodes_sauvegardes + 1}/{dataset_config.nb_episodes}")
                utils_lerobot.jouer_son_debut_episode()

                record_loop(
                    robot=robot,
                    events=events,
                    fps=camera.fps,
                    teleop_action_processor=teleop_action_processor,
                    robot_action_processor=robot_action_processor,
                    robot_observation_processor=robot_observation_processor,
                    teleop=teleop,
                    dataset=dataset,
                    control_time_s=int(dataset_config.duree_episode_s),
                    single_task=tache,
                    display_data=False,
                )

                if events["rerecord_episode"]:
                    events["rerecord_episode"] = False
                    events["exit_early"] = False
                    dataset.clear_episode_buffer()
                    print("Épisode annulé. Réinitialisation.")
                    utils_lerobot.jouer_son_annulation_episode()
                    sleep(DELAI_APRES_ANNULATION_S)

                    if not events["stop_recording"]:
                        utils_lerobot.jouer_son_reinitialisation()

                        record_loop(
                            robot=robot,
                            events=events,
                            fps=camera.fps,
                            teleop_action_processor=teleop_action_processor,
                            robot_action_processor=robot_action_processor,
                            robot_observation_processor=robot_observation_processor,
                            teleop=teleop,
                            control_time_s=int(dataset_config.duree_reinitialisation_s),
                            single_task=tache,
                            display_data=False,
                        )

                    continue

                utils_lerobot.jouer_son_fin_episode()
                print("Épisode terminé. Sauvegarde en cours...")

                dataset.save_episode()
                episodes_sauvegardes += 1

                print(f"Épisode sauvegardé : {episodes_sauvegardes}/{dataset_config.nb_episodes}")

                if (
                    episodes_sauvegardes < dataset_config.nb_episodes
                    and not events["stop_recording"]
                ):
                    print("Réinitialisation")
                    utils_lerobot.jouer_son_reinitialisation()

                    record_loop(
                        robot=robot,
                        events=events,
                        fps=camera.fps,
                        teleop_action_processor=teleop_action_processor,
                        robot_action_processor=robot_action_processor,
                        robot_observation_processor=robot_observation_processor,
                        teleop=teleop,
                        control_time_s=int(dataset_config.duree_reinitialisation_s),
                        single_task=tache,
                        display_data=False,
                    )

            if episodes_sauvegardes == dataset_config.nb_episodes:
                utils_lerobot.jouer_son_fin_entrainement()

    except KeyboardInterrupt:
        print("Interruption clavier.")

    finally:
        if listener is not None:
            listener.stop()

        restaurer_echo_terminal(attributs_terminal)

        if dataset is not None:
            try:
                dataset.finalize()

            except Exception as erreur:  # noqa: BLE001 - la déconnexion reste prioritaire.
                print(f"ATTENTION : finalisation incomplète ({erreur})")

        if teleop.is_connected:
            teleop.disconnect()

        if robot.is_connected:
            robot.disconnect()

    print("Terminé.")


if __name__ == "__main__":
    enregistrer_dataset()
