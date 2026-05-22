"""
Évaluer plusieurs fois une politique LeRobot sur le robot réel.

Le script charge une politique une seule fois, connecte le bras follower et la caméra globale,
puis attend un appui sur Espace pour lancer chaque essai. 
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from select import select
from threading import Event
from time import perf_counter
from typing import Iterator
import sys
import termios
import tty

from lerobot.cameras import CameraConfig
from lerobot.cameras.opencv import OpenCVCameraConfig
from lerobot.configs import PreTrainedConfig
from lerobot.robots.so_follower import SO101FollowerConfig
from lerobot.rollout.configs import BaseStrategyConfig, RolloutConfig
from lerobot.rollout.context import RolloutContext, build_rollout_context
from lerobot.rollout.strategies.core import send_next_action
from lerobot.utils.action_interpolator import ActionInterpolator
from lerobot.utils.robot_utils import precise_sleep

from commun import config_lerobot
from commun import utils

CHEMIN_CONFIG = Path(__file__).resolve().parent / "config_lerobot_ws.toml"

TOUCHE_ESPACE = " "
TOUCHE_ECHAP = "\x1b"
TOUCHE_ENTREE = "\n"
TOUCHE_QUITTER = "q"


@contextmanager
def mode_clavier_direct() -> Iterator[bool]:
    """
    Lire une touche sans attendre Entrée quand le terminal le permet.

    Le booléen produit indique si le mode direct a été activé. Dans le terminal intégré VSCode,
    ce mode fonctionne généralement, mais un repli avec Entrée reste disponible si `stdin`
    n'est pas un TTY.
    """

    if not sys.stdin.isatty():
        yield False
        return

    descripteur = sys.stdin.fileno()
    attributs = termios.tcgetattr(descripteur)

    try:
        tty.setcbreak(descripteur)
        yield True

    finally:
        termios.tcsetattr(descripteur, termios.TCSADRAIN, attributs)


def saisir_nom_entrainement(racine_entrainements: Path, nom_defaut: str) -> str:
    """
    Demander le nom du dossier d'entraînement à utiliser.
    """

    while True:
        nom = utils.saisir_avec_texte_defaut("Nom de la politique : ", nom_defaut).strip()

        if nom:
            return nom

        print("Le nom ne peut pas être vide.")
        print(f"Dossier attendu : {racine_entrainements}")


def chemin_politique(
    config: config_lerobot.ConfigLeRobotWs,
    nom_entrainement: str,
) -> Path:
    """
    Construire le chemin du modèle `pretrained_model` à partir du nom saisi.
    """

    racine_entrainements = config.entrainement.dossier_sortie_absolu(config.workspace)

    dossier_checkpoints = racine_entrainements / nom_entrainement / "checkpoints"
    chemin_last = dossier_checkpoints / "last" / "pretrained_model"

    if chemin_last.exists():
        return chemin_last

    if not dossier_checkpoints.exists():
        return chemin_last

    checkpoints_numeriques = sorted(
        chemin
        for chemin in dossier_checkpoints.iterdir()
        if chemin.is_dir() and chemin.name.isdecimal() and (chemin / "pretrained_model").exists()
    )

    if checkpoints_numeriques:
        return checkpoints_numeriques[-1] / "pretrained_model"

    return chemin_last


def afficher_modeles_disponibles(racine_entrainements: Path) -> None:
    """
    Afficher les entraînements locaux qui contiennent au moins un modèle préentraîné.
    """

    if not racine_entrainements.exists():
        print(f"Dossier d'entraînements introuvable : {racine_entrainements}")
        return

    chemins_modeles = sorted(racine_entrainements.glob("*/checkpoints/*/pretrained_model"))

    if not chemins_modeles:
        print(f"Aucun modèle trouvé sous : {racine_entrainements}")
        return

    print("Politiques disponibles :")

    for chemin_modele in chemins_modeles:
        nom_politique = chemin_modele.parents[2].name
        checkpoint = chemin_modele.parent.name
        print(f"- {nom_politique} ({checkpoint})")


def creer_config_robot(config: config_lerobot.ConfigLeRobotWs) -> SO101FollowerConfig:
    """
    Créer la configuration du follower SO-101 avec la caméra globale.
    """

    camera = config.materiel.camera_globale
    robot = config.materiel.robot
    cameras: dict[str, CameraConfig] = {
        camera.nom: OpenCVCameraConfig(
            index_or_path=camera.chemin,
            width=camera.largeur,
            height=camera.hauteur,
            fps=camera.fps,
            fourcc=camera.fourcc,
        )
    }

    return SO101FollowerConfig(
        port=robot.port_follower,
        id=robot.id_follower,
        cameras=cameras,
    )


def creer_config_rollout(
    config: config_lerobot.ConfigLeRobotWs,
    chemin_modele: Path,
) -> RolloutConfig:
    """
    Préparer la configuration LeRobot utilisée pour le rollout réel.
    """

    execution = config.execution_politique
    config_politique = PreTrainedConfig.from_pretrained(chemin_modele)
    config_politique.pretrained_path = chemin_modele

    if execution.strategie != "base":
        raise ValueError("Ce script prend seulement en charge `strategie = \"base\"`.")

    return RolloutConfig(
        robot=creer_config_robot(config),
        policy=config_politique,
        strategy=BaseStrategyConfig(),
        fps=float(config.materiel.camera_globale.fps),
        duration=execution.duree_s,
        interpolation_multiplier=execution.interpolation_multiplier,
        task=execution.tache_defaut,
        display_data=execution.display_data,
    )


def deconnecter_contexte(contexte: RolloutContext) -> None:
    """
    Arrêter l'inférence et déconnecter le matériel déjà ouvert.
    """

    try:
        contexte.policy.inference.stop()

    finally:
        robot = contexte.hardware.robot_wrapper.inner
        teleop = contexte.hardware.teleop

        if teleop is not None and teleop.is_connected:
            teleop.disconnect()

        if robot.is_connected:
            robot.disconnect()


def touche_directe_disponible() -> str | None:
    """
    Lire une touche déjà disponible, sans bloquer la boucle de contrôle.
    """

    pret, _, _ = select([sys.stdin], [], [], 0)

    if not pret:
        return None

    return sys.stdin.read(1)


def ramener_position_initiale(
    contexte: RolloutContext,
    duree_s: float = 3.0,
    fps: int = 50,
) -> None:
    """
    Ramener doucement le robot à sa position initiale de connexion.
    """

    position_initiale = contexte.hardware.initial_position

    if not position_initiale:
        print("Position initiale indisponible, retour ignoré.")
        return

    robot = contexte.hardware.robot_wrapper
    observation_courante = robot.get_observation()
    position_courante = {
        cle: valeur for cle, valeur in observation_courante.items() if cle in position_initiale
    }
    nb_etapes = max(int(duree_s * fps), 1)

    print("Retour en position initiale.")

    for etape in range(1, nb_etapes + 1):
        ratio = etape / nb_etapes
        action = {}

        for cle, valeur_depart in position_courante.items():
            valeur_arrivee = position_initiale[cle]
            action[cle] = valeur_depart * (1 - ratio) + valeur_arrivee * ratio

        robot.send_action(action)
        precise_sleep(1 / fps)


def executer_essai(contexte: RolloutContext, clavier_direct: bool) -> None:
    """
    Exécuter un essai autonome avec la même logique de boucle que `lerobot_rollout`.
    """

    config = contexte.runtime.cfg
    moteur_inference = contexte.policy.inference
    robot = contexte.hardware.robot_wrapper
    interpolateur = ActionInterpolator(multiplier=config.interpolation_multiplier)
    intervalle_controle = interpolateur.get_control_interval(config.fps)
    depart = perf_counter()

    moteur_inference.reset()
    moteur_inference.resume()

    try:
        while not contexte.runtime.shutdown_event.is_set():
            debut_boucle = perf_counter()

            if config.duration > 0 and (perf_counter() - depart) >= config.duration:
                break

            if clavier_direct and touche_directe_disponible() == TOUCHE_ECHAP:
                contexte.runtime.shutdown_event.set()
                break

            observation = robot.get_observation()
            observation_traitee = contexte.processors.robot_observation_processor(observation)
            moteur_inference.notify_observation(observation_traitee)

            send_next_action(
                observation_traitee,
                observation,
                contexte,
                interpolateur,
            )

            duree_boucle = perf_counter() - debut_boucle
            attente_s = intervalle_controle - duree_boucle

            if attente_s > 0:
                precise_sleep(attente_s)

    finally:
        moteur_inference.pause()
        ramener_position_initiale(contexte)


def lire_touche_directe() -> str:
    """
    Attendre et lire une touche en mode direct.
    """

    while True:
        pret, _, _ = select([sys.stdin], [], [])

        if pret:
            return sys.stdin.read(1)


def lire_commande_repli() -> str:
    """
    Lire une commande simple si la lecture directe n'est pas disponible.
    """

    commande = input("Entrée : lancer un essai | q puis Entrée : quitter > ").strip().lower()

    if commande == TOUCHE_QUITTER:
        return TOUCHE_ECHAP

    return TOUCHE_ESPACE


def afficher_resume(config: config_lerobot.ConfigLeRobotWs, chemin_modele: Path) -> None:
    """
    Afficher les informations utiles avant la boucle interactive.
    """

    execution = config.execution_politique

    print(f"Tâche : {execution.tache_defaut}")
    print(f"Durée : {execution.duree_s:g} s")
    print("Espace : lancer un essai | ESC : quitter")


def boucle_interactive(config: config_lerobot.ConfigLeRobotWs, chemin_modele: Path) -> None:
    """
    Connecter le robot puis lancer un essai à chaque appui sur Espace.
    """

    evenement_arret = Event()
    contexte: RolloutContext | None = None
    numero_essai = 0

    try:
        config_rollout = creer_config_rollout(config, chemin_modele)
        contexte = build_rollout_context(config_rollout, evenement_arret)
        contexte.policy.inference.start()

        afficher_resume(config, chemin_modele)

        with mode_clavier_direct() as clavier_direct:
            while not evenement_arret.is_set():
                touche = lire_touche_directe() if clavier_direct else lire_commande_repli()

                if touche == TOUCHE_ECHAP:
                    evenement_arret.set()
                    break

                if touche not in (TOUCHE_ESPACE, TOUCHE_ENTREE):
                    continue

                numero_essai += 1
                print(f"Essai {numero_essai} lancé.")

                try:
                    executer_essai(contexte, clavier_direct)
                    print(f"Essai {numero_essai} terminé.")

                except Exception as erreur:  # noqa: BLE001 - le matériel doit rester maîtrisé.
                    print(f"Erreur pendant l'essai {numero_essai} : {erreur}")
                    print("Arrêt par sécurité.")
                    evenement_arret.set()

    except KeyboardInterrupt:
        print()
        print("Interruption clavier.")
        evenement_arret.set()

    finally:
        if contexte is not None:
            deconnecter_contexte(contexte)

    print("Terminé.")


def main() -> None:
    """
    Point d'entrée du script.
    """

    config = config_lerobot.charger_config(CHEMIN_CONFIG)
    racine_entrainements = config.entrainement.dossier_sortie_absolu(config.workspace)
    nom_entrainement = saisir_nom_entrainement(
        racine_entrainements,
        config.execution_politique.nom_politique_defaut,
    )
    chemin_modele = chemin_politique(config, nom_entrainement)

    if not chemin_modele.exists():
        print(f"Modèle introuvable : {chemin_modele}")
        afficher_modeles_disponibles(racine_entrainements)
        return

    boucle_interactive(config, chemin_modele)


if __name__ == "__main__":
    main()
