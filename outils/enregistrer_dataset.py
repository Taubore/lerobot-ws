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

import argparse
import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime
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
from commun import utils_lerobot

CHOIX_ANNULER = "1"
CHOIX_SUPPRIMER = "2"
CHOIX_PROCHAIN_LOT = "3"
PREFIXE_CAMERA = "observation.images."
STATUT_BRUT = "brut"
STATUT_TERMINE = "termine"
STATUT_INTERROMPU = "interrompu"
REPONSE_ANNULER = "q"
NOMBRE_MAX_LOTS = 999
NOM_MANIFESTE = "session_lot.json"
CHAMP_INDEX_DEBUT = "from"


@dataclass(frozen=True)
class ParametresCamera:
    """
    Paramètres utiles pour la caméra globale OpenCV/V4L2.
    """

    nom: str
    chemin: Path
    largeur: int
    hauteur: int
    fps: int
    fourcc: str


@dataclass(frozen=True)
class ParametresRobot:
    """
    Paramètres utiles pour les deux bras SO-101.
    """

    port_leader: str
    port_follower: str
    id_leader: str
    id_follower: str


@dataclass(frozen=True)
class ParametresSession:
    """
    Paramètres effectifs d'une session d'enregistrement.
    """

    repo_id: str
    tache: str
    nb_episodes: int
    duree_episode_s: float
    duree_reinitialisation_s: float
    delai_avant_demarrage_s: int
    use_videos: bool
    image_writer_threads: int
    push_to_hub: bool
    camera: ParametresCamera
    robot: ParametresRobot


@dataclass(frozen=True)
class OptionsCli:
    """
    Options de ligne de commande qui complètent la configuration TOML.
    """

    nouveau_lot: bool
    dry_run: bool


def analyser_arguments() -> argparse.Namespace:
    """
    Lire les arguments optionnels qui remplacent ponctuellement le TOML.
    """

    analyseur = argparse.ArgumentParser(
        description="Enregistrer un lot brut LeRobot dans le cache local Hugging Face."
    )
    analyseur.add_argument("--repo-id", help="Repo id du lot brut à créer.")
    analyseur.add_argument("--tache", help="Tâche unique enregistrée dans le dataset.")
    analyseur.add_argument("--episodes", type=int, help="Nombre d'épisodes à enregistrer.")
    analyseur.add_argument("--duree-episode", type=float, help="Durée d'un épisode en secondes.")
    analyseur.add_argument(
        "--duree-reinitialisation",
        type=float,
        help="Durée d'une phase de réinitialisation en secondes.",
    )
    analyseur.add_argument(
        "--delai-demarrage",
        type=int,
        help="Délai avant le début de l'enregistrement en secondes.",
    )
    analyseur.add_argument("--largeur", type=int, help="Largeur de la caméra globale.")
    analyseur.add_argument("--hauteur", type=int, help="Hauteur de la caméra globale.")
    analyseur.add_argument("--fps", type=int, help="FPS de la caméra et du dataset.")
    analyseur.add_argument("--fourcc", help="Code FourCC OpenCV/V4L2 de la caméra.")
    analyseur.add_argument(
        "--nouveau-lot",
        action="store_true",
        help="Créer automatiquement le prochain lot libre avec un suffixe numérique.",
    )
    analyseur.add_argument(
        "--dry-run",
        action="store_true",
        help="Afficher le résumé sans connecter le robot, la caméra ni le clavier.",
    )

    return analyseur.parse_args()


def valeur_ou_defaut[T](valeur: T | None, defaut: T) -> T:
    """
    Garder la valeur CLI quand elle existe, sinon revenir au TOML.
    """

    if valeur is None:
        return defaut

    return valeur


def creer_parametres_session(
    config: config_lerobot.ConfigLeRobotWs,
    arguments: argparse.Namespace,
) -> tuple[ParametresSession, OptionsCli]:
    """
    Combiner le TOML et les remplacements fournis en CLI.
    """

    camera_config = config.materiel.camera_globale
    robot_config = config.materiel.robot
    dataset_config = config.enregistrement.dataset

    camera = ParametresCamera(
        nom=camera_config.nom,
        chemin=camera_config.chemin,
        largeur=valeur_ou_defaut(arguments.largeur, camera_config.largeur),
        hauteur=valeur_ou_defaut(arguments.hauteur, camera_config.hauteur),
        fps=valeur_ou_defaut(arguments.fps, camera_config.fps),
        fourcc=valeur_ou_defaut(arguments.fourcc, camera_config.fourcc),
    )
    robot = ParametresRobot(
        port_leader=robot_config.port_leader,
        port_follower=robot_config.port_follower,
        id_leader=robot_config.id_leader,
        id_follower=robot_config.id_follower,
    )
    session = ParametresSession(
        repo_id=valeur_ou_defaut(arguments.repo_id, dataset_config.repo_id_defaut),
        tache=valeur_ou_defaut(arguments.tache, dataset_config.tache_defaut),
        nb_episodes=valeur_ou_defaut(arguments.episodes, dataset_config.nb_episodes),
        duree_episode_s=valeur_ou_defaut(
            arguments.duree_episode,
            dataset_config.duree_episode_s,
        ),
        duree_reinitialisation_s=valeur_ou_defaut(
            arguments.duree_reinitialisation,
            dataset_config.duree_reinitialisation_s,
        ),
        delai_avant_demarrage_s=valeur_ou_defaut(
            arguments.delai_demarrage,
            config.enregistrement.delai_avant_demarrage_s,
        ),
        use_videos=dataset_config.use_videos,
        image_writer_threads=dataset_config.image_writer_threads,
        push_to_hub=dataset_config.push_to_hub,
        camera=camera,
        robot=robot,
    )
    options = OptionsCli(nouveau_lot=arguments.nouveau_lot, dry_run=arguments.dry_run)

    return session, options


def creer_robot(parametres: ParametresSession) -> SO101Follower:
    """
    Créer le bras suiveur avec la caméra globale.
    """

    camera_globale = parametres.camera

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
        port=parametres.robot.port_follower,
        id=parametres.robot.id_follower,
        cameras=cameras,
    )

    return SO101Follower(config_robot)


def creer_teleop(parametres: ParametresSession) -> SO101Leader:
    """
    Créer le bras leader utilisé pour la téléopération.
    """

    config_teleop = SO101LeaderConfig(
        port=parametres.robot.port_leader,
        id=parametres.robot.id_leader,
    )

    return SO101Leader(config_teleop)


def creer_dataset(robot: SO101Follower, parametres: ParametresSession) -> LeRobotDataset:
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
        use_videos=parametres.use_videos,
    )
    observation_features = aggregate_pipeline_dataset_features(
        pipeline=robot_observation_processor,
        initial_features=create_initial_features(observation=robot.observation_features),
        use_videos=parametres.use_videos,
    )
    dataset_features = combine_feature_dicts(action_features, observation_features)

    return LeRobotDataset.create(
        repo_id=parametres.repo_id,
        fps=parametres.camera.fps,
        features=dataset_features,
        robot_type=robot.name,
        use_videos=parametres.use_videos,
        image_writer_threads=parametres.image_writer_threads,
    )


def chemin_dataset_cache(repo_id: str) -> Path:
    """
    Retourner l'emplacement local par défaut du dataset LeRobot.
    """

    return HF_LEROBOT_HOME / repo_id


def chemin_est_dans_cache_lerobot(chemin: Path) -> bool:
    """
    Vérifier qu'un chemin résolu reste sous le cache local LeRobot.
    """

    try:
        chemin.resolve().relative_to(HF_LEROBOT_HOME.resolve())

    except ValueError:
        return False

    return True


def supprimer_dataset_cache(repo_id: str) -> None:
    """
    Supprimer un dataset brut existant dans le cache LeRobot.
    """

    chemin_dataset = chemin_dataset_cache(repo_id).resolve()

    if not chemin_est_dans_cache_lerobot(chemin_dataset):
        raise ValueError("Refus de supprimer un dossier hors de HF_LEROBOT_HOME.")

    shutil.rmtree(chemin_dataset)
    print("Suppression du dataset brut effectuée.")


def generer_repo_id_lot(base_repo_id: str) -> str:
    """
    Générer le prochain repo_id disponible avec un suffixe `_001`, `_002`, etc.
    """

    for numero_lot in range(1, NOMBRE_MAX_LOTS + 1):
        repo_id = f"{base_repo_id}_{numero_lot:03d}"

        if not chemin_dataset_cache(repo_id).exists():
            return repo_id

    raise RuntimeError(f"Aucun lot disponible trouvé après {NOMBRE_MAX_LOTS} essais.")


def choisir_repo_id_disponible(parametres: ParametresSession, nouveau_lot: bool) -> str | None:
    """
    Déterminer le repo_id final sans écraser accidentellement un lot existant.
    """

    if nouveau_lot:
        return generer_repo_id_lot(parametres.repo_id)

    if not chemin_dataset_cache(parametres.repo_id).exists():
        return parametres.repo_id

    print(f"Le lot existe déjà : {chemin_dataset_cache(parametres.repo_id)}")
    print("Que souhaitez-vous faire ?")
    print("1 : annuler")
    print("2 : supprimer et recommencer")
    print("3 : utiliser le prochain lot disponible")
    print("TODO : ajouter une reprise seulement si l'API LeRobot la garantit clairement.")

    choix = input("Votre choix [1/2/3] : ").strip()

    if choix == CHOIX_ANNULER:
        return None

    if choix == CHOIX_SUPPRIMER:
        supprimer_dataset_cache(parametres.repo_id)
        return parametres.repo_id

    if choix == CHOIX_PROCHAIN_LOT:
        return generer_repo_id_lot(parametres.repo_id)

    print("Choix non reconnu. Annulation par sécurité.")
    return None


def remplacer_repo_id(parametres: ParametresSession, repo_id: str) -> ParametresSession:
    """
    Retourner des paramètres identiques avec un autre repo_id.
    """

    return ParametresSession(
        repo_id=repo_id,
        tache=parametres.tache,
        nb_episodes=parametres.nb_episodes,
        duree_episode_s=parametres.duree_episode_s,
        duree_reinitialisation_s=parametres.duree_reinitialisation_s,
        delai_avant_demarrage_s=parametres.delai_avant_demarrage_s,
        use_videos=parametres.use_videos,
        image_writer_threads=parametres.image_writer_threads,
        push_to_hub=parametres.push_to_hub,
        camera=parametres.camera,
        robot=parametres.robot,
    )


def afficher_resume_session(parametres: ParametresSession) -> None:
    """
    Afficher les paramètres importants avant toute connexion matérielle.
    """

    print("Enregistrement d'un lot brut LeRobot")
    print(f"Repo id : {parametres.repo_id}")
    print(f"Tâche : {parametres.tache}")
    print(f"Nombre d'épisodes : {parametres.nb_episodes}")
    print(f"Durée épisode : {parametres.duree_episode_s} s")
    print(f"Durée réinitialisation : {parametres.duree_reinitialisation_s} s")
    print(f"Délai de démarrage : {parametres.delai_avant_demarrage_s} s")
    print("Caméra :")
    print(f"- {parametres.camera.nom} : {parametres.camera.chemin}")
    print(f"- {parametres.camera.largeur}x{parametres.camera.hauteur}")
    print(f"- {parametres.camera.fps} FPS, FourCC {parametres.camera.fourcc}")
    print("Robots :")
    print(f"- leader : {parametres.robot.id_leader} sur {parametres.robot.port_leader}")
    print(f"- follower : {parametres.robot.id_follower} sur {parametres.robot.port_follower}")
    print(f"Stockage : {chemin_dataset_cache(parametres.repo_id)}")
    print(f"Upload Hub : {parametres.push_to_hub}")
    print("Contrôles LeRobot :")
    print("- Flèche droite : accepter l'épisode ou passer à l'étape suivante.")
    print("- Flèche gauche : annuler et recommencer l'épisode courant.")
    print("- Échap : arrêter, encoder les vidéos et terminer proprement.")
    print()


def confirmer_demarrage() -> bool:
    """
    Demander une confirmation simple juste avant la connexion au matériel.
    """

    reponse = input("Entrée pour démarrer, q pour annuler : ").strip().lower()
    return reponse != REPONSE_ANNULER


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


def donnees_manifeste_initial(parametres: ParametresSession) -> dict[str, Any]:
    """
    Construire le manifeste minimal d'un lot brut.
    """

    return {
        "repo_id": parametres.repo_id,
        "tache": parametres.tache,
        "date_heure_locale_iso": datetime.now().astimezone().isoformat(timespec="seconds"),
        "nb_episodes_demandes": parametres.nb_episodes,
        "duree_episode_s": parametres.duree_episode_s,
        "duree_reinitialisation_s": parametres.duree_reinitialisation_s,
        "camera": {
            **asdict(parametres.camera),
            "chemin": str(parametres.camera.chemin),
        },
        "robot": asdict(parametres.robot),
        "statut": STATUT_BRUT,
    }


def ecrire_manifeste(chemin_dataset: Path, donnees: dict[str, Any]) -> None:
    """
    Écrire le manifeste JSON lisible par un humain.
    """

    chemin_manifeste = chemin_dataset / NOM_MANIFESTE
    chemin_manifeste.write_text(
        json.dumps(donnees, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def lire_attribut(objet: object, noms: tuple[str, ...], defaut: Any = None) -> Any:
    """
    Lire le premier attribut existant dans une liste de noms possibles.
    """

    for nom in noms:
        if hasattr(objet, nom):
            return getattr(objet, nom)

    return defaut


def extraire_champs_camera(dataset_lu: LeRobotDataset) -> list[str]:
    """
    Extraire les champs caméra connus depuis les features du dataset.
    """

    features = lire_attribut(dataset_lu, ("features",), {})

    if not isinstance(features, dict):
        return []

    return sorted(champ for champ in features if champ.startswith(PREFIXE_CAMERA))


def compter_episodes_lus(dataset_lu: LeRobotDataset) -> int:
    """
    Compter les épisodes avec les attributs LeRobot courants quand ils sont disponibles.
    """

    nombre = lire_attribut(dataset_lu, ("num_episodes", "num_episode", "n_episodes"))

    if isinstance(nombre, int):
        return nombre

    meta = lire_attribut(dataset_lu, ("meta",))
    nombre_meta = lire_attribut(meta, ("total_episodes", "num_episodes")) if meta else None

    if isinstance(nombre_meta, int):
        return nombre_meta

    episode_data_index = lire_attribut(dataset_lu, ("episode_data_index",), {})

    if isinstance(episode_data_index, dict) and CHAMP_INDEX_DEBUT in episode_data_index:
        return len(episode_data_index[CHAMP_INDEX_DEBUT])

    return 0


def valider_dataset_court(repo_id: str) -> None:
    """
    Relire brièvement le dataset finalisé pour détecter les problèmes évidents.
    """

    print("Validation courte du dataset finalisé :")

    try:
        dataset_lu = LeRobotDataset(repo_id)
        nb_episodes = compter_episodes_lus(dataset_lu)
        nb_frames = len(dataset_lu)
        fps = lire_attribut(dataset_lu, ("fps",), "inconnu")
        champs_camera = extraire_champs_camera(dataset_lu)

    except Exception as erreur:  # noqa: BLE001 - diagnostic court en fin de session.
        print(f"- dataset lisible : ATTENTION ({erreur})")
        return

    print("- dataset lisible : OK")
    print(f"- épisodes lus : {nb_episodes}")
    print(f"- frames : {nb_frames}")
    print(f"- FPS : {fps}")
    print(f"- champs caméra détectés : {champs_camera}")


def enregistrer_dataset() -> None:
    """
    Enregistrer les épisodes d'un lot brut dans le cache LeRobot.
    """

    arguments = analyser_arguments()
    config = config_lerobot.charger_config()
    parametres, options = creer_parametres_session(config, arguments)

    if parametres.push_to_hub:
        raise ValueError("Ce script d'enregistrement brut doit garder `push_to_hub = false`.")

    repo_id = choisir_repo_id_disponible(parametres, options.nouveau_lot)

    if repo_id is None:
        print("Session annulée.")
        return

    parametres = remplacer_repo_id(parametres, repo_id)
    afficher_resume_session(parametres)

    if options.dry_run:
        print("Mode dry-run : arrêt avant toute connexion matérielle.")
        return

    if not confirmer_demarrage():
        print("Session annulée.")
        return

    camera_v4l2.initialiser_camera_arducam(
        camera=str(parametres.camera.chemin),
        largeur=parametres.camera.largeur,
        hauteur=parametres.camera.hauteur,
        fps=parametres.camera.fps,
    )

    robot = creer_robot(parametres)
    teleop = creer_teleop(parametres)
    dataset = None
    listener = None
    episodes_sauvegardes = 0
    chemin_dataset = chemin_dataset_cache(parametres.repo_id)
    manifeste = donnees_manifeste_initial(parametres)

    try:
        robot.connect()
        teleop.connect()
        listener, events = init_keyboard_listener()
        dataset = creer_dataset(robot, parametres)
        ecrire_manifeste(chemin_dataset, manifeste)

        (
            teleop_action_processor,
            robot_action_processor,
            robot_observation_processor,
        ) = make_default_processors()

        attendre_demarrage(parametres.delai_avant_demarrage_s)

        with VideoEncodingManager(dataset):
            while episodes_sauvegardes < parametres.nb_episodes and not events["stop_recording"]:
                print(f"----- Épisode {episodes_sauvegardes + 1}/{parametres.nb_episodes} -----")
                utils_lerobot.jouer_son_debut_episode()

                record_loop(
                    robot=robot,
                    events=events,
                    fps=parametres.camera.fps,
                    teleop_action_processor=teleop_action_processor,
                    robot_action_processor=robot_action_processor,
                    robot_observation_processor=robot_observation_processor,
                    teleop=teleop,
                    dataset=dataset,
                    control_time_s=int(parametres.duree_episode_s),
                    single_task=parametres.tache,
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
                            fps=parametres.camera.fps,
                            teleop_action_processor=teleop_action_processor,
                            robot_action_processor=robot_action_processor,
                            robot_observation_processor=robot_observation_processor,
                            teleop=teleop,
                            control_time_s=int(parametres.duree_reinitialisation_s),
                            single_task=parametres.tache,
                            display_data=False,
                        )

                    continue

                dataset.save_episode()
                episodes_sauvegardes += 1
                print(f"Épisode sauvegardé : {episodes_sauvegardes}/{parametres.nb_episodes}")
                utils_lerobot.jouer_son_fin_episode()

                if episodes_sauvegardes < parametres.nb_episodes and not events["stop_recording"]:
                    print("Réinitialisation")
                    utils_lerobot.jouer_son_reinitialisation()

                    record_loop(
                        robot=robot,
                        events=events,
                        fps=parametres.camera.fps,
                        teleop_action_processor=teleop_action_processor,
                        robot_action_processor=robot_action_processor,
                        robot_observation_processor=robot_observation_processor,
                        teleop=teleop,
                        control_time_s=int(parametres.duree_reinitialisation_s),
                        single_task=parametres.tache,
                        display_data=False,
                    )

    except KeyboardInterrupt:
        print("Interruption clavier.")

    finally:
        if dataset is not None:
            try:
                dataset.finalize()
                valider_dataset_court(parametres.repo_id)

            except Exception as erreur:  # noqa: BLE001 - déconnexion prioritaire.
                print(f"ATTENTION : finalisation incomplète ({erreur})")

            statut = STATUT_TERMINE

            if episodes_sauvegardes < parametres.nb_episodes:
                statut = STATUT_INTERROMPU

            manifeste["nb_episodes_sauvegardes"] = episodes_sauvegardes
            manifeste["statut"] = statut
            ecrire_manifeste(chemin_dataset, manifeste)

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
