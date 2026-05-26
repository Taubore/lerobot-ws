"""
Enregistrer un lot brut local de dataset LeRobot.

Ce script crée un lot dans le cache LeRobot :
`~/.cache/huggingface/lerobot/{repo_id}`.

Les étapes d'inspection, d'officialisation, de fusion et d'entraînement sont volontairement
laissées à d'autres scripts.
"""

import os
import select
import shutil
import sys
import termios
from contextlib import contextmanager
from pathlib import Path
from time import sleep
from typing import Any, Iterator

import numpy as np

from lerobot.cameras import Camera, CameraConfig, ColorMode, Cv2Rotation, make_cameras_from_configs
from lerobot.cameras.opencv import OpenCVCameraConfig
from lerobot.cameras.realsense import RealSenseCameraConfig
from lerobot.common.control_utils import init_keyboard_listener
from lerobot.datasets import (
    LeRobotDataset,
    VideoEncodingManager,
    aggregate_pipeline_dataset_features,
    create_initial_features,
)
from lerobot.processor import make_default_processors
from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig
from lerobot.scripts.lerobot_record import init_rerun, record_loop
from lerobot.teleoperators.so_leader import SO101Leader, SO101LeaderConfig
from lerobot.types import RobotAction, RobotObservation
from lerobot.utils.constants import HF_LEROBOT_HOME
from lerobot.utils.feature_utils import combine_feature_dicts
from lerobot.utils.visualization_utils import log_rerun_data as log_rerun_data_lerobot

from commun import camera_v4l2
from commun import config_lerobot
from commun import utils
from commun import utils_lerobot

CHOIX_ANNULER = "1"
CHOIX_SUPPRIMER = "2"
CHOIX_NOUVEAU_NOM = "3"
DELAI_APRES_ANNULATION_S = 2.0
CHEMIN_CONFIG = Path(__file__).resolve().parent / "config_lerobot_ws.toml"
BACKEND_OPENCV = "opencv"
BACKEND_REALSENSE = "realsense"
CHEMIN_RERUN_DEUX_CAMERAS = "cameras/deux_cameras"
CLE_CAMERA_GLOBALE = "globale"
CLE_CAMERA_PINCE = "pince"
DELAI_APERCU_CAMERA_S = 1.0 / 15.0
VERBOSE = False


@contextmanager
def sortie_lerobot_discrete() -> Iterator[None]:
    """
    Masquer les sorties verbeuses de LeRobot et de ses encodeurs natifs.
    """

    if VERBOSE:
        yield
        return

    sys.stdout.flush()
    sys.stderr.flush()

    stdout = sys.stdout.fileno()
    stderr = sys.stderr.fileno()
    stdout_sauvegarde = os.dup(stdout)
    stderr_sauvegarde = os.dup(stderr)

    with open(os.devnull, "w", encoding="utf-8") as sortie_nulle:
        try:
            os.dup2(sortie_nulle.fileno(), stdout)
            os.dup2(sortie_nulle.fileno(), stderr)
            yield

        finally:
            sys.stdout.flush()
            sys.stderr.flush()
            os.dup2(stdout_sauvegarde, stdout)
            os.dup2(stderr_sauvegarde, stderr)
            os.close(stdout_sauvegarde)
            os.close(stderr_sauvegarde)


@contextmanager
def encodage_video_discret(dataset: LeRobotDataset) -> Iterator[None]:
    """
    Gérer l'encodage vidéo en masquant seulement les journaux internes.
    """

    gestionnaire = VideoEncodingManager(dataset)

    with sortie_lerobot_discrete():
        gestionnaire.__enter__()

    try:
        yield

    except BaseException:
        type_erreur, erreur, trace = sys.exc_info()

        with sortie_lerobot_discrete():
            erreur_masquee = gestionnaire.__exit__(type_erreur, erreur, trace)

        if not erreur_masquee:
            raise

    else:
        with sortie_lerobot_discrete():
            gestionnaire.__exit__(None, None, None)


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

    if attributs is not None:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, attributs)


def normaliser_image_rerun(valeur: Any) -> np.ndarray | None:
    """
    Retourner une image compatible Rerun si la valeur ressemble à une image.
    """

    if not isinstance(valeur, np.ndarray):
        return None

    image = valeur

    if image.ndim == 3 and image.shape[0] in (1, 3, 4) and image.shape[-1] not in (1, 3, 4):
        image = np.transpose(image, (1, 2, 0))

    if image.ndim != 3:
        return None

    return image


def composer_image_deux_cameras(observation: RobotObservation) -> np.ndarray | None:
    """
    Composer une image unique avec la caméra globale à gauche et la pince à droite.
    """

    image_globale = normaliser_image_rerun(observation.get(CLE_CAMERA_GLOBALE))
    image_pince = normaliser_image_rerun(observation.get(CLE_CAMERA_PINCE))

    if image_globale is None or image_pince is None:
        return None

    if image_globale.shape[0] != image_pince.shape[0]:
        return None

    return np.concatenate((image_globale, image_pince), axis=1)


def journaliser_image_deux_cameras(image_deux_cameras: np.ndarray) -> None:
    """
    Envoyer l'image composite des deux caméras vers Rerun.
    """

    import rerun as rr

    rr.log(CHEMIN_RERUN_DEUX_CAMERAS, rr.Image(image_deux_cameras))


def journaliser_donnees_rerun(
    observation: RobotObservation | None = None,
    action: RobotAction | None = None,
    compress_images: bool = False,
) -> None:
    """
    Journaliser les données LeRobot et une vue composite des deux caméras.
    """

    log_rerun_data_lerobot(
        observation=observation,
        action=action,
        compress_images=compress_images,
    )

    if observation is None:
        return

    image_deux_cameras = composer_image_deux_cameras(observation)

    if image_deux_cameras is not None:
        journaliser_image_deux_cameras(image_deux_cameras)


def activer_affichage_deux_cameras_rerun() -> None:
    """
    Remplacer localement la journalisation Rerun utilisée par `record_loop`.
    """

    record_loop.__globals__["log_rerun_data"] = journaliser_donnees_rerun


def configurer_vue_deux_cameras_rerun() -> None:
    """
    Configurer Rerun pour afficher les deux caméras côte à côte.
    """

    import rerun as rr
    import rerun.blueprint as rrb

    rr.send_blueprint(
        rrb.Blueprint(
            rrb.Spatial2DView(
                origin=CHEMIN_RERUN_DEUX_CAMERAS,
                name="Caméras globale et pince",
            ),
            collapse_panels=True,
        )
    )


def creer_configs_cameras_dataset(
    config: config_lerobot.ConfigLeRobotWs,
) -> dict[str, CameraConfig]:
    """
    Créer les configurations LeRobot des caméras du dataset.
    """

    return {
        camera.nom: creer_config_camera_dataset(camera)
        for camera in config.materiel.cameras_dataset.values()
    }


def initialiser_cameras_opencv_v4l2(config: config_lerobot.ConfigLeRobotWs) -> None:
    """
    Appliquer la configuration V4L2 aux caméras OpenCV du dataset.
    """

    for camera in config.materiel.cameras_dataset.values():
        if camera.backend != BACKEND_OPENCV:
            continue

        if camera.chemin is None:
            raise ValueError(f"La caméra `{camera.nom}` exige un chemin OpenCV.")

        camera_v4l2.initialiser_camera_arducam(
            camera=str(camera.chemin),
            largeur=camera.largeur,
            hauteur=camera.hauteur,
            fps=camera.fps,
        )


def lire_observation_cameras(cameras: dict[str, Camera]) -> RobotObservation:
    """
    Lire une image sur chaque caméra connectée.
    """

    return {nom_camera: camera.read() for nom_camera, camera in cameras.items()}


def entree_disponible() -> bool:
    """
    Indiquer si l'utilisateur a appuyé sur Entrée dans le terminal.
    """

    if not sys.stdin.isatty():
        return True

    lecture, _ecriture, _erreur = select.select([sys.stdin], [], [], 0)

    return bool(lecture)


def afficher_apercu_cameras(config: config_lerobot.ConfigLeRobotWs) -> None:
    """
    Afficher les deux caméras dans Rerun avant les prompts d'enregistrement.
    """

    cameras = make_cameras_from_configs(creer_configs_cameras_dataset(config))

    try:
        for camera in cameras.values():
            camera.connect()

        print("Aperçu des caméras actif dans Rerun.")
        print("Ajuster le cadrage, puis appuyer sur Entrée pour continuer.")

        while True:
            observation = lire_observation_cameras(cameras)
            image_deux_cameras = composer_image_deux_cameras(observation)

            if image_deux_cameras is not None:
                journaliser_image_deux_cameras(image_deux_cameras)

            if entree_disponible():
                if sys.stdin.isatty():
                    sys.stdin.readline()
                break

            sleep(DELAI_APERCU_CAMERA_S)

    finally:
        for camera in cameras.values():
            if camera.is_connected:
                camera.disconnect()


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
    Créer le bras SO101 follower avec les caméras du dataset.
    """

    robot = config.materiel.robot

    config_robot = SO101FollowerConfig(
        port=robot.port_follower,
        id=robot.id_follower,
        cameras=creer_configs_cameras_dataset(config),
    )

    return SO101Follower(config_robot)


def creer_config_camera_dataset(camera: config_lerobot.ConfigCameraDataset) -> CameraConfig:
    """
    Créer la configuration LeRobot correspondant au backend caméra demandé.
    """

    if camera.backend == BACKEND_REALSENSE:
        if camera.serial is None:
            raise ValueError(f"La caméra `{camera.nom}` exige un numéro de série RealSense.")

        return RealSenseCameraConfig(
            serial_number_or_name=camera.serial,
            width=camera.largeur,
            height=camera.hauteur,
            fps=camera.fps,
            color_mode=ColorMode.RGB,
            use_depth=camera.use_depth,
            rotation=Cv2Rotation.NO_ROTATION,
            warmup_s=3,
        )

    if camera.backend == BACKEND_OPENCV:
        if camera.chemin is None:
            raise ValueError(f"La caméra `{camera.nom}` exige un chemin OpenCV.")

        return OpenCVCameraConfig(
            index_or_path=camera.chemin,
            width=camera.largeur,
            height=camera.hauteur,
            fps=camera.fps,
            fourcc=camera.fourcc,
            color_mode=ColorMode.RGB,
            rotation=Cv2Rotation.NO_ROTATION,
        )

    raise ValueError(f"Backend caméra non supporté : {camera.backend}")


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
        fps=fps_enregistrement(config),
        features=combine_feature_dicts(action_features, observation_features),
        robot_type=robot.name,
        use_videos=dataset_config.use_videos,
        image_writer_threads=dataset_config.image_writer_threads,
    )


def fps_enregistrement(config: config_lerobot.ConfigLeRobotWs) -> int:
    """
    Retourner le FPS commun de l'enregistrement.

    La RealSense validée fonctionne à 15 FPS. Le dataset utilise donc le plus petit FPS caméra
    pour éviter de demander une cadence supérieure à une caméra disponible.
    """

    return min(camera.fps for camera in config.materiel.cameras_dataset.values())


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

        choix = utils.saisir_ligne("Votre choix [1/2/3] : ").strip()

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

    config = config_lerobot.charger_config(CHEMIN_CONFIG)
    dataset_config = config.enregistrement.dataset
    fps_dataset = fps_enregistrement(config)

    if dataset_config.push_to_hub:
        raise ValueError("Ce script exige `push_to_hub = false` dans `config_lerobot_ws.toml`.")

    initialiser_cameras_opencv_v4l2(config)

    if config.enregistrement.display_data:
        with sortie_lerobot_discrete():
            init_rerun(session_name="recording")
        activer_affichage_deux_cameras_rerun()
        configurer_vue_deux_cameras_rerun()
        afficher_apercu_cameras(config)

    repo_id = choisir_repo_dataset(config)

    if repo_id is None:
        print("Session annulée.")
        return

    tache = saisir_texte("Tâche : ", dataset_config.tache_defaut)
    afficher_demarrage(repo_id, tache)

    robot = creer_robot(config)
    teleop = creer_teleop(config)
    dataset: LeRobotDataset | None = None
    listener = None
    attributs_terminal = None
    episodes_sauvegardes = 0

    try:
        attributs_terminal = desactiver_echo_terminal()
        robot.connect()
        teleop.connect()
        listener, events = init_keyboard_listener()
        with sortie_lerobot_discrete():
            dataset = creer_dataset(robot, config, repo_id)
        assert dataset is not None

        (
            teleop_action_processor,
            robot_action_processor,
            robot_observation_processor,
        ) = make_default_processors()

        attendre_demarrage(config.enregistrement.delai_avant_demarrage_s)

        with encodage_video_discret(dataset):
            while (
                episodes_sauvegardes < dataset_config.nb_episodes
                and not events["stop_recording"]
            ):
                print(f"Épisode {episodes_sauvegardes + 1}/{dataset_config.nb_episodes}")
                utils_lerobot.jouer_son_debut_episode()

                with sortie_lerobot_discrete():
                    record_loop(
                        robot=robot,
                        events=events,
                        fps=fps_dataset,
                        teleop_action_processor=teleop_action_processor,
                        robot_action_processor=robot_action_processor,
                        robot_observation_processor=robot_observation_processor,
                        teleop=teleop,
                        dataset=dataset,
                        control_time_s=int(dataset_config.duree_episode_s),
                        single_task=tache,
                        display_data=config.enregistrement.display_data,
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

                        with sortie_lerobot_discrete():
                            record_loop(
                                robot=robot,
                                events=events,
                                fps=fps_dataset,
                                teleop_action_processor=teleop_action_processor,
                                robot_action_processor=robot_action_processor,
                                robot_observation_processor=robot_observation_processor,
                                teleop=teleop,
                                control_time_s=int(dataset_config.duree_reinitialisation_s),
                                single_task=tache,
                                display_data=config.enregistrement.display_data,
                            )

                    continue

                utils_lerobot.jouer_son_fin_episode()
                print("Épisode terminé. Sauvegarde en cours...")

                with sortie_lerobot_discrete():
                    dataset.save_episode()
                episodes_sauvegardes += 1

                print(f"Épisode sauvegardé : {episodes_sauvegardes}/{dataset_config.nb_episodes}")

                if not events["stop_recording"]:
                    print("Réinitialisation")
                    utils_lerobot.jouer_son_reinitialisation()

                    with sortie_lerobot_discrete():
                        record_loop(
                            robot=robot,
                            events=events,
                            fps=fps_dataset,
                            teleop_action_processor=teleop_action_processor,
                            robot_action_processor=robot_action_processor,
                            robot_observation_processor=robot_observation_processor,
                            teleop=teleop,
                            control_time_s=int(dataset_config.duree_reinitialisation_s),
                            single_task=tache,
                            display_data=config.enregistrement.display_data,
                        )

            if episodes_sauvegardes == dataset_config.nb_episodes:
                utils_lerobot.jouer_son_fin_dataset()

    except KeyboardInterrupt:
        print("Interruption clavier.")

    finally:
        if listener is not None:
            listener.stop()

        restaurer_echo_terminal(attributs_terminal)

        if dataset is not None:
            try:
                with sortie_lerobot_discrete():
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
