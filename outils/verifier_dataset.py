"""
Vérifier un dataset LeRobot local et écrire un manifeste humain.
"""

from dataclasses import dataclass
from datetime import datetime
from math import ceil
from pathlib import Path
from statistics import mean, median
from typing import Any

from lerobot.datasets import LeRobotDataset
from lerobot.utils.constants import HF_LEROBOT_HOME

from commun import config_lerobot
from commun import utils


CHOIX_CACHE = "1"
CHOIX_WORKSPACE = "2"
MARGE_DUREE_EXECUTION_S = 0.5
PREFIXE_CAMERA = "observation.images."
PREFIXE_CAMERA_VIDEO = "observation.videos."
TEXTE_NON_DISPONIBLE = "Non disponible"
TEXTE_OUI = "Oui"
TEXTE_NON = "Non"


@dataclass(frozen=True)
class OrigineDataset:
    """
    Décrit une origine locale de dataset.
    """

    choix: str
    libelle: str
    racine: Path


@dataclass(frozen=True)
class EpisodeDuree:
    """
    Résumé de durée pour un épisode.
    """

    episode: int
    nb_frames: int
    duree_s: float


@dataclass(frozen=True)
class StatistiquesDurees:
    """
    Statistiques de durée des épisodes.
    """

    episodes: list[EpisodeDuree]
    duree_min_s: float
    duree_max_s: float
    duree_moyenne_s: float
    duree_mediane_s: float
    suggestion_duree_s: int


def charger_configuration() -> config_lerobot.ConfigLeRobotWs:
    """
    Charger la configuration du workspace.
    """

    return config_lerobot.charger_config()


def racine_workspace_datasets(config: config_lerobot.ConfigLeRobotWs) -> Path:
    """
    Retourner la racine contenant les datasets officialisés.
    """

    return config.workspace.racine / "datasets"


def demander_origine_dataset(config: config_lerobot.ConfigLeRobotWs) -> OrigineDataset:
    """
    Demander l'origine locale du dataset à vérifier.
    """

    origines = {
        CHOIX_CACHE: OrigineDataset(
            choix=CHOIX_CACHE,
            libelle="cache LeRobot",
            racine=HF_LEROBOT_HOME,
        ),
        CHOIX_WORKSPACE: OrigineDataset(
            choix=CHOIX_WORKSPACE,
            libelle="workspace",
            racine=racine_workspace_datasets(config),
        ),
    }

    print("Origine du dataset")
    print("------------------")
    print("1. cache LeRobot")
    print("2. workspace")

    try:
        choix = input("Votre choix [1] : ").strip()
    except EOFError:
        choix = ""

    if not choix:
        choix = CHOIX_CACHE

    if choix not in origines:
        raise ValueError("Origine invalide : choisir 1 pour le cache ou 2 pour le workspace.")

    return origines[choix]


def demander_repo_id(repo_id_defaut: str) -> str:
    """
    Demander le repo_id à vérifier.
    """

    try:
        return utils.saisir_avec_texte_defaut(
            "Repo_id du dataset à vérifier : ",
            repo_id_defaut,
        ).strip()
    except EOFError:
        return repo_id_defaut


def valider_repo_id(repo_id: str) -> None:
    """
    Valider un repo_id simple de type utilisateur/dataset.
    """

    if not repo_id:
        raise ValueError("Repo_id vide.")

    if "/" not in repo_id:
        raise ValueError("Repo_id invalide : format attendu utilisateur/dataset.")

    if repo_id.startswith("/"):
        raise ValueError("Repo_id invalide : chemin absolu interdit.")

    if ".." in repo_id:
        raise ValueError("Repo_id invalide : '..' interdit.")


def construire_chemin_dataset(origine: OrigineDataset, repo_id: str) -> Path:
    """
    Construire le chemin local du dataset.
    """

    return origine.racine / repo_id


def verifier_chemin_dataset(origine: OrigineDataset, repo_id: str, chemin: Path) -> None:
    """
    Vérifier que le chemin local existe avant le chargement.
    """

    if chemin.exists():
        return

    message = f"""
Dataset introuvable.

Origine choisie : {origine.libelle}
Repo ID         : {repo_id}
Chemin calculé : {chemin}

Suggestion : vérifier si le dataset est dans le cache LeRobot ou dans workspace/datasets.
"""
    raise FileNotFoundError(message.strip())


def charger_dataset(repo_id: str, racine: Path) -> LeRobotDataset:
    """
    Charger le dataset LeRobot depuis son chemin local.
    """

    return LeRobotDataset(repo_id=repo_id, root=racine)


def formater_booleen(valeur: bool) -> str:
    """
    Convertir un booléen en texte français court.
    """

    return TEXTE_OUI if valeur else TEXTE_NON


def formater_valeur(valeur: object | None) -> str:
    """
    Convertir une valeur optionnelle en texte lisible.
    """

    if valeur is None:
        return TEXTE_NON_DISPONIBLE

    return str(valeur)


def formater_duree(duree_s: float | None) -> str:
    """
    Formater une durée en secondes.
    """

    if duree_s is None:
        return TEXTE_NON_DISPONIBLE

    return f"{duree_s:.2f} s"


def dimensions_feature(features: dict[str, Any], nom_feature: str) -> str:
    """
    Retourner les dimensions déclarées d'une feature si elles sont disponibles.
    """

    feature = features.get(nom_feature)

    if not isinstance(feature, dict):
        return TEXTE_NON_DISPONIBLE

    dimensions = feature.get("shape")

    if dimensions is None:
        return TEXTE_NON_DISPONIBLE

    return str(dimensions)


def lister_cameras(features: dict[str, Any]) -> list[str]:
    """
    Lister les clés caméra détectées dans les features.
    """

    return sorted(
        cle
        for cle in features
        if cle.startswith(PREFIXE_CAMERA) or cle.startswith(PREFIXE_CAMERA_VIDEO)
    )


def compter_fichiers_video(racine: Path) -> int | None:
    """
    Compter les fichiers vidéo si le dossier existe.
    """

    dossier_videos = racine / "videos"

    if not dossier_videos.exists():
        return None

    return len(list(dossier_videos.rglob("*.mp4")))


def detecter_format_video(racine: Path) -> str:
    """
    Détecter les extensions vidéo présentes sans inspecter les fichiers.
    """

    dossier_videos = racine / "videos"

    if not dossier_videos.exists():
        return TEXTE_NON_DISPONIBLE

    extensions = sorted(
        {chemin.suffix.lower() for chemin in dossier_videos.rglob("*") if chemin.is_file()}
    )
    extensions = [extension for extension in extensions if extension]

    if not extensions:
        return TEXTE_NON_DISPONIBLE

    return ", ".join(extensions)


def convertir_entier(valeur: Any) -> int:
    """
    Convertir une valeur scalaire Python, NumPy ou Torch en entier.
    """

    if isinstance(valeur, int):
        return valeur

    if isinstance(valeur, float | str):
        return int(valeur)

    methode_item = getattr(valeur, "item", None)

    if callable(methode_item):
        return convertir_entier(methode_item())

    raise TypeError(f"Valeur non convertible en entier : {valeur!r}")


def calculer_durees_episodes(dataset: LeRobotDataset) -> StatistiquesDurees:
    """
    Calculer les durées d'épisodes à partir du nombre de frames et du FPS.
    """

    fps = getattr(dataset, "fps", None)

    if not isinstance(fps, (int, float)) or fps <= 0:
        raise ValueError("FPS indisponible ou invalide : impossible de calculer les durées.")

    frames_par_episode: dict[int, int] = {}

    for index_frame in range(dataset.num_frames):
        item = dataset.get_raw_item(index_frame)
        episode = convertir_entier(item["episode_index"])
        frames_par_episode[episode] = frames_par_episode.get(episode, 0) + 1

    episodes = [
        EpisodeDuree(
            episode=episode,
            nb_frames=nb_frames,
            duree_s=nb_frames / fps,
        )
        for episode, nb_frames in sorted(frames_par_episode.items())
    ]

    if not episodes:
        raise ValueError("Aucun épisode détecté : impossible de calculer les durées.")

    durees = [episode.duree_s for episode in episodes]
    duree_max_s = max(durees)

    return StatistiquesDurees(
        episodes=episodes,
        duree_min_s=min(durees),
        duree_max_s=duree_max_s,
        duree_moyenne_s=mean(durees),
        duree_mediane_s=median(durees),
        suggestion_duree_s=ceil(duree_max_s + MARGE_DUREE_EXECUTION_S),
    )


def afficher_resume_dataset(
    origine: OrigineDataset,
    repo_id: str,
    racine: Path,
    dataset: LeRobotDataset,
) -> None:
    """
    Afficher le résumé technique du dataset.
    """

    features = dict(dataset.features)
    cles_features = set(features)
    cles_cameras = lister_cameras(features)
    videos_presentes = (racine / "videos").exists()

    print("\nDataset")
    print("-------")
    print(f"Origine       : {origine.libelle}")
    print(f"Repo ID       : {repo_id}")
    print(f"Chemin local  : {racine}")
    print(f"Chargement    : OK")
    print(f"Épisodes      : {dataset.num_episodes}")
    print(f"Frames        : {dataset.num_frames}")
    print(f"FPS           : {formater_valeur(getattr(dataset, 'fps', None))}")
    print(f"État          : {presence_feature(cles_features, 'observation.state')}")
    print(f"Action        : {presence_feature(cles_features, 'action')}")
    print(f"Timestamp     : {presence_feature(cles_features, 'timestamp')}")
    print(f"Frame index   : {presence_feature(cles_features, 'frame_index')}")
    print(f"Episode index : {presence_feature(cles_features, 'episode_index')}")
    print(f"Task index    : {presence_feature(cles_features, 'task_index')}")
    print(f"Caméras       : {', '.join(cles_cameras) if cles_cameras else 'indisponible'}")
    print(f"Vidéos        : {'présentes' if videos_presentes else 'indisponibles'}")


def presence_feature(cles_features: set[str], nom_feature: str) -> str:
    """
    Formater la présence d'une feature.
    """

    return "présent" if nom_feature in cles_features else "indisponible"


def afficher_statistiques_durees(dataset: LeRobotDataset, statistiques: StatistiquesDurees) -> None:
    """
    Afficher les statistiques de durée des épisodes.
    """

    print("\nStatistiques des épisodes")
    print("-------------------------")
    print(f"Épisodes       : {dataset.num_episodes}")
    print(f"Frames totales : {dataset.num_frames}")
    print(f"FPS            : {getattr(dataset, 'fps', TEXTE_NON_DISPONIBLE)}")
    print(f"Durée minimale : {formater_duree(statistiques.duree_min_s)}")
    print(f"Durée maximale : {formater_duree(statistiques.duree_max_s)}")
    print(f"Durée moyenne  : {formater_duree(statistiques.duree_moyenne_s)}")
    print(f"Durée médiane  : {formater_duree(statistiques.duree_mediane_s)}")

    print("\nDétail")
    print("------")
    for episode in statistiques.episodes:
        print(
            f"Épisode {episode.episode:02d} : "
            f"{episode.nb_frames} frames, {episode.duree_s:.2f} s"
        )


def afficher_avertissements(statistiques: StatistiquesDurees) -> None:
    """
    Afficher les avertissements simples sur les durées.
    """

    ecart_s = statistiques.duree_max_s - statistiques.duree_min_s
    seuil_court_s = statistiques.duree_mediane_s * 0.75
    episodes_courts = [
        episode for episode in statistiques.episodes if episode.duree_s < seuil_court_s
    ]

    if ecart_s <= 1.0 and not episodes_courts:
        return

    print("\nAvertissements")
    print("--------------")

    if ecart_s > 1.0:
        print(f"- Écart supérieur à 1 seconde entre l'épisode le plus court et le plus long.")

    for episode in episodes_courts:
        print(
            f"- Épisode {episode.episode:02d} beaucoup plus court que la médiane : "
            f"{episode.duree_s:.2f} s."
        )


def suggerer_duree_execution(statistiques: StatistiquesDurees) -> None:
    """
    Afficher une suggestion pour la durée d'exécution de politique.
    """

    print("\nSuggestion pour duree_s")
    print("-----------------------")
    print(
        "Suggestion pour [execution_politique].duree_s : "
        f"{statistiques.suggestion_duree_s}"
    )
    print(
        f"Base : durée maximale {statistiques.duree_max_s:.2f} s "
        f"+ marge {MARGE_DUREE_EXECUTION_S:.2f} s"
    )


def lister_taches(dataset: LeRobotDataset) -> str:
    """
    Lister les tâches disponibles si LeRobot les expose simplement.
    """

    tasks = getattr(dataset.meta, "tasks", None)

    if isinstance(tasks, dict):
        valeurs = [str(valeur) for valeur in tasks.values()]
        return ", ".join(valeurs) if valeurs else TEXTE_NON_DISPONIBLE

    if isinstance(tasks, list):
        valeurs = [str(valeur) for valeur in tasks]
        return ", ".join(valeurs) if valeurs else TEXTE_NON_DISPONIBLE

    return TEXTE_NON_DISPONIBLE


def creer_contenu_manifest(
    origine: OrigineDataset,
    repo_id: str,
    racine: Path,
    dataset: LeRobotDataset,
    statistiques: StatistiquesDurees,
) -> str:
    """
    Créer le contenu Markdown du manifeste de vérification.
    """

    features = dict(dataset.features)
    cles_features = set(features)
    cles_cameras = lister_cameras(features)
    fps = getattr(dataset, "fps", None)
    robot_type = getattr(dataset.meta, "robot_type", None)
    images_presentes = (racine / "images").exists()
    videos_presentes = (racine / "videos").exists()
    observations_presentes = any(cle.startswith("observation.") for cle in features)
    cameras_detectees = len(cles_cameras) > 0
    donnees_visuelles_presentes = images_presentes or videos_presentes or cameras_detectees
    features_texte = ", ".join(sorted(features)) if features else TEXTE_NON_DISPONIBLE
    cameras_texte = ", ".join(cles_cameras) if cles_cameras else TEXTE_NON_DISPONIBLE
    lignes_episodes = "\n".join(
        f"| {episode.episode:02d} | {episode.nb_frames} | {episode.duree_s:.2f} s |"
        for episode in statistiques.episodes
    )

    return f"""# Manifeste de vérification LeRobot

## Résumé

| Champ | Valeur |
| --- | --- |
| Dataset | {repo_id} |
| Origine | {origine.libelle} |
| Statut de vérification | OK |
| Date de vérification | {datetime.now().isoformat(timespec="seconds")} |
| Chemin local | {racine} |

## Chargement

| Contrôle | Résultat |
| --- | --- |
| Chargement avec `LeRobotDataset` | OK |
| Dataset lisible | Oui |
| Épisodes détectés | {formater_booleen(dataset.num_episodes > 0)} |
| Frames détectées | {formater_booleen(dataset.num_frames > 0)} |

## Structure détectée

| Champ | Valeur |
| --- | --- |
| Nombre d'épisodes | {dataset.num_episodes} |
| Nombre de frames | {dataset.num_frames} |
| FPS | {formater_valeur(fps)} |
| Robot type | {formater_valeur(robot_type)} |
| Tâches disponibles | {lister_taches(dataset)} |
| Features principales | {features_texte} |

## Données robotiques

| Contrôle | Résultat |
| --- | --- |
| Présence de `observation.state` | {formater_booleen("observation.state" in cles_features)} |
| Présence de `action` | {formater_booleen("action" in cles_features)} |
| Présence de `timestamp` | {formater_booleen("timestamp" in cles_features)} |
| Présence de `frame_index` | {formater_booleen("frame_index" in cles_features)} |
| Présence de `episode_index` | {formater_booleen("episode_index" in cles_features)} |
| Présence de `task_index` | {formater_booleen("task_index" in cles_features)} |
| Dimensions de `observation.state` | {dimensions_feature(features, "observation.state")} |
| Dimensions de `action` | {dimensions_feature(features, "action")} |
| Observations détectées | {formater_booleen(observations_presentes)} |

## Données visuelles

| Champ | Valeur |
| --- | --- |
| Présence d'images ou vidéos | {formater_booleen(donnees_visuelles_presentes)} |
| Caméras détectées | {cameras_texte} |
| Format vidéo détecté | {detecter_format_video(racine)} |
| Nombre de fichiers vidéo | {formater_valeur(compter_fichiers_video(racine))} |

## Statistiques des épisodes

| Champ | Valeur |
| --- | --- |
| Durée minimale | {formater_duree(statistiques.duree_min_s)} |
| Durée maximale | {formater_duree(statistiques.duree_max_s)} |
| Durée moyenne | {formater_duree(statistiques.duree_moyenne_s)} |
| Durée médiane | {formater_duree(statistiques.duree_mediane_s)} |

## Détail par épisode

| Épisode | Frames | Durée |
| --- | ---: | ---: |
{lignes_episodes}

## Suggestion pour `[execution_politique].duree_s`

| Champ | Valeur |
| --- | --- |
| Suggestion | {statistiques.suggestion_duree_s} |
| Base | Durée maximale {statistiques.duree_max_s:.2f} s + marge {MARGE_DUREE_EXECUTION_S:.2f} s |

## Conclusion

- Verdict final : OK
- Notes : vérifier manuellement les avertissements affichés dans la console si nécessaire.
"""


def ecrire_manifest(chemin_dataset: Path, contenu: str) -> Path:
    """
    Écrire ou remplacer le manifeste Markdown dans le dossier du dataset.
    """

    chemin_manifest = chemin_dataset / "manifeste.md"
    chemin_manifest.write_text(contenu, encoding="utf-8")
    return chemin_manifest


def verifier_dataset(
    origine: OrigineDataset,
    repo_id: str,
    racine: Path,
) -> bool:
    """
    Charger le dataset, afficher la vérification et écrire le manifeste.
    """

    try:
        verifier_chemin_dataset(origine, repo_id, racine)
        dataset = charger_dataset(repo_id, racine)
        statistiques = calculer_durees_episodes(dataset)
    except Exception as erreur:  # noqa: BLE001
        print("\nChargement ou vérification : ERREUR")
        print(f"Erreur : {erreur}")
        print("\nVerdict : ERREUR")
        return False

    afficher_resume_dataset(origine, repo_id, racine, dataset)
    afficher_statistiques_durees(dataset, statistiques)
    afficher_avertissements(statistiques)
    suggerer_duree_execution(statistiques)

    contenu_manifest = creer_contenu_manifest(origine, repo_id, racine, dataset, statistiques)
    chemin_manifest = ecrire_manifest(racine, contenu_manifest)

    print("\nVérification")
    print("------------")
    print("Verdict   : OK")
    print(f"Manifeste : {chemin_manifest}")
    return True


def main() -> None:
    """
    Point d'entrée du script.
    """

    print("Vérification du dataset LeRobot\n")

    try:
        config = charger_configuration()
        origine = demander_origine_dataset(config)
        repo_id = demander_repo_id(config.enregistrement.dataset.repo_id_defaut)
        valider_repo_id(repo_id)
        racine = construire_chemin_dataset(origine, repo_id)
    except ValueError as erreur:
        print(f"\nVerdict : ERREUR\nErreur  : {erreur}")
        return

    verifier_dataset(origine, repo_id, racine)


if __name__ == "__main__":
    main()
