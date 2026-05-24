"""
Lire la configuration locale des scripts LeRobot du workspace.

Le fichier TOML garde les valeurs modifiables hors des scripts. Les dataclasses donnent ensuite
des accès typés et lisibles côté Python, compatibles avec le niveau Pylance standard.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import tomllib

CHEMIN_CONFIG_DEFAUT = Path(__file__).resolve().parents[1] / "outils" / "config_lerobot_ws.toml"


@dataclass(frozen=True)
class ConfigRobot:
    """
    Configuration des bras SO-101.
    """

    port_leader: str
    port_follower: str
    id_leader: str
    id_follower: str


@dataclass(frozen=True)
class ConfigCamera:
    """
    Configuration de la caméra globale.
    """

    nom: str
    chemin: Path
    largeur: int
    hauteur: int
    fps: int
    fourcc: str


@dataclass(frozen=True)
class ConfigDatasetEnregistrement:
    """
    Configuration propre au lot de dataset à enregistrer.
    """

    repo_id_defaut: str
    tache_defaut: str
    nb_episodes: int
    duree_episode_s: float
    duree_reinitialisation_s: float
    use_videos: bool
    image_writer_threads: int
    push_to_hub: bool


@dataclass(frozen=True)
class ConfigWorkspace:
    """
    Configuration des chemins principaux du workspace local.
    """

    racine: Path


@dataclass(frozen=True)
class ConfigEntrainement:
    """
    Configuration commune aux entraînements locaux.
    """

    dossier_sortie: Path

    def dossier_sortie_absolu(self, workspace: ConfigWorkspace) -> Path:
        """
        Retourner le dossier d'entraînement en chemin absolu.
        """

        if self.dossier_sortie.is_absolute():
            return self.dossier_sortie

        return workspace.racine / self.dossier_sortie


@dataclass(frozen=True)
class ConfigExecutionPolitique:
    """
    Configuration pour exécuter une politique entraînée sur le robot réel.
    """

    strategie: str
    nom_politique_defaut: str
    duree_s: float
    tache_defaut: str
    display_data: bool
    interpolation_multiplier: int


@dataclass(frozen=True)
class ConfigEnregistrement:
    """
    Configuration de la session d'enregistrement.
    """

    delai_avant_demarrage_s: int
    display_data: bool
    dataset: ConfigDatasetEnregistrement


@dataclass(frozen=True)
class ConfigMateriel:
    """
    Configuration matérielle commune.
    """

    robot: ConfigRobot
    camera_globale: ConfigCamera


@dataclass(frozen=True)
class ConfigLeRobotWs:
    """
    Configuration complète du workspace LeRobot.
    """

    workspace: ConfigWorkspace
    materiel: ConfigMateriel
    enregistrement: ConfigEnregistrement
    entrainement: ConfigEntrainement
    execution_politique: ConfigExecutionPolitique


def charger_config(chemin: Path = CHEMIN_CONFIG_DEFAUT) -> ConfigLeRobotWs:
    """
    Charger la configuration TOML du workspace.
    """

    with chemin.open("rb") as fichier:
        donnees = tomllib.load(fichier)

    return ConfigLeRobotWs(
        workspace=_charger_workspace(donnees),
        materiel=_charger_materiel(donnees),
        enregistrement=_charger_enregistrement(donnees),
        entrainement=_charger_entrainement(donnees),
        execution_politique=_charger_execution_politique(donnees),
    )


def _charger_workspace(donnees: dict[str, Any]) -> ConfigWorkspace:
    workspace = donnees["workspace"]

    return ConfigWorkspace(
        racine=Path(workspace["racine"]),
    )


def _charger_materiel(donnees: dict[str, Any]) -> ConfigMateriel:
    materiel = donnees["materiel"]
    robot = materiel["robot"]
    camera = materiel["camera_globale"]

    return ConfigMateriel(
        robot=ConfigRobot(
            port_leader=robot["port_leader"],
            port_follower=robot["port_follower"],
            id_leader=robot["id_leader"],
            id_follower=robot["id_follower"],
        ),
        camera_globale=ConfigCamera(
            nom=camera["nom"],
            chemin=Path(camera["chemin"]),
            largeur=camera["largeur"],
            hauteur=camera["hauteur"],
            fps=camera["fps"],
            fourcc=camera["fourcc"],
        ),
    )


def _charger_entrainement(donnees: dict[str, Any]) -> ConfigEntrainement:
    entrainement = donnees["entrainement"]

    return ConfigEntrainement(
        dossier_sortie=Path(entrainement["dossier_sortie"]),
    )


def _charger_execution_politique(donnees: dict[str, Any]) -> ConfigExecutionPolitique:
    execution_politique = donnees["execution_politique"]

    return ConfigExecutionPolitique(
        strategie=execution_politique["strategie"],
        nom_politique_defaut=execution_politique["nom_politique_defaut"],
        duree_s=execution_politique["duree_s"],
        tache_defaut=execution_politique["tache_defaut"],
        display_data=execution_politique["display_data"],
        interpolation_multiplier=execution_politique["interpolation_multiplier"],
    )


def _charger_enregistrement(donnees: dict[str, Any]) -> ConfigEnregistrement:
    enregistrement = donnees["enregistrement"]
    dataset = enregistrement["dataset"]

    return ConfigEnregistrement(
        delai_avant_demarrage_s=enregistrement["delai_avant_demarrage_s"],
        display_data=enregistrement["display_data"],
        dataset=ConfigDatasetEnregistrement(
            repo_id_defaut=dataset["repo_id_defaut"],
            tache_defaut=dataset["tache_defaut"],
            nb_episodes=dataset["nb_episodes"],
            duree_episode_s=dataset["duree_episode_s"],
            duree_reinitialisation_s=dataset["duree_reinitialisation_s"],
            use_videos=dataset["use_videos"],
            image_writer_threads=dataset["image_writer_threads"],
            push_to_hub=dataset["push_to_hub"],
        ),
    )
