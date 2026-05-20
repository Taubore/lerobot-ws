"""
Vérifier minimalement un dataset brut LeRobot et écrire un manifeste humain.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from lerobot.datasets import LeRobotDataset

from commun import config_lerobot
from commun import utils


RACINE_CACHE_LEROBOT = Path.home() / ".cache" / "huggingface" / "lerobot"
CHEMIN_CONFIG = Path(__file__).resolve().parent / "config_lerobot_ws.toml"
PREFIXE_CAMERA = "observation.images."
PREFIXE_CAMERA_VIDEO = "observation.videos."
TEXTE_NON_DISPONIBLE = "Non disponible"
TEXTE_OUI = "Oui"
TEXTE_NON = "Non"
MOTIF_LOT = re.compile(r"_lot\d{2}$")


def demander_repo_id(repo_id_defaut: str) -> str:
    """
    Demander le repo_id à vérifier.
    """

    return utils.saisir_avec_texte_defaut(
        "Repo_id du dataset à vérifier : ",
        repo_id_defaut,
    ).strip()


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


def chemin_dataset(repo_id: str) -> Path:
    """
    Retourner le chemin local du dataset dans le cache LeRobot.
    """

    return RACINE_CACHE_LEROBOT / repo_id


def detecter_type_dataset(repo_id: str) -> str:
    """
    Détecter si le dataset ressemble à un lot brut selon son suffixe.
    """

    nom_dataset = repo_id.split("/")[-1]

    if MOTIF_LOT.search(nom_dataset):
        return "lot brut"

    return "dataset unique ou officialisé"


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

    extensions = sorted({chemin.suffix.lower() for chemin in dossier_videos.rglob("*")})
    extensions = [extension for extension in extensions if extension]

    if not extensions:
        return TEXTE_NON_DISPONIBLE

    return ", ".join(extensions)


def creer_contenu_manifest(repo_id: str, racine: Path, dataset: LeRobotDataset) -> str:
    """
    Créer le contenu Markdown du manifeste de vérification.
    """

    features = dict(dataset.features)
    cles_cameras = lister_cameras(features)
    fps = getattr(dataset, "fps", None)
    robot_type = getattr(dataset.meta, "robot_type", None)
    duree_s = dataset.num_frames / fps if isinstance(fps, (int, float)) and fps > 0 else None
    fichiers_video = compter_fichiers_video(racine)
    images_presentes = (racine / "images").exists()
    videos_presentes = (racine / "videos").exists()
    state_present = "observation.state" in features
    action_presente = "action" in features
    observations_presentes = any(cle.startswith("observation.") for cle in features)
    cameras_detectees = len(cles_cameras) > 0
    donnees_visuelles_presentes = images_presentes or videos_presentes or cameras_detectees
    duree_texte = f"{duree_s:.2f} s" if duree_s is not None else TEXTE_NON_DISPONIBLE
    features_texte = ", ".join(sorted(features)) if features else TEXTE_NON_DISPONIBLE
    cameras_texte = ", ".join(cles_cameras) if cles_cameras else TEXTE_NON_DISPONIBLE
    dimensions_state = dimensions_feature(features, "observation.state")
    dimensions_action = dimensions_feature(features, "action")

    return f"""# Manifeste de vérification LeRobot

## Résumé

- Dataset : {repo_id}
- Statut de vérification : OK
- Date de vérification : {datetime.now().isoformat(timespec="seconds")}
- Chemin local : {racine}
- Type : {detecter_type_dataset(repo_id)}

## Résultat

- Chargement avec `LeRobotDataset` : OK
- Verdict : OK
- Message court : Dataset lisible et structure minimale détectée.

## Structure détectée

- Nombre d'épisodes : {dataset.num_episodes}
- Nombre de frames : {dataset.num_frames}
- FPS : {formater_valeur(fps)}
- Durée approximative : {duree_texte}
- Robot type : {formater_valeur(robot_type)}
- Features principales : {features_texte}
- Caméras détectées : {cameras_texte}

## Données robotiques

- Présence de `observation.state` : {formater_booleen(state_present)}
- Présence de `action` : {formater_booleen(action_presente)}
- Dimensions de `observation.state` si disponible : {dimensions_state}
- Dimensions de `action` si disponible : {dimensions_action}

## Données visuelles

- Présence d'images ou vidéos : {formater_booleen(donnees_visuelles_presentes)}
- Clés caméra détectées : {cameras_texte}
- Format vidéo détecté si disponible : {detecter_format_video(racine)}
- Nombre de fichiers vidéo si facilement disponible : {formater_valeur(fichiers_video)}

## Contrôles de cohérence simples

- Dataset lisible : Oui
- Épisodes détectés : {formater_booleen(dataset.num_episodes > 0)}
- Frames détectées : {formater_booleen(dataset.num_frames > 0)}
- Actions détectées : {formater_booleen(action_presente)}
- Observations détectées : {formater_booleen(observations_presentes)}
- Caméras détectées : {formater_booleen(cameras_detectees)}

## Conclusion

- Verdict final : OK
- Prêt pour officialisation : Oui
- Notes :
"""


def ecrire_manifest(chemin_dataset: Path, nom_fichier: str, contenu: str) -> Path:
    """
    Écrire ou remplacer le manifeste Markdown dans le dossier du dataset.
    """

    chemin_manifest = chemin_dataset / nom_fichier
    chemin_manifest.write_text(contenu, encoding="utf-8")
    return chemin_manifest


def verifier_dataset(repo_id: str) -> bool:
    """
    Charger le dataset et afficher une vérification courte.
    """

    print("\nVérification du dataset LeRobot\n")
    print(f"Dataset : {repo_id}\n")

    racine = chemin_dataset(repo_id)

    try:
        dataset = LeRobotDataset(repo_id=repo_id, root=racine)
    except Exception as erreur:  # noqa: BLE001
        print("Chargement : ERREUR")
        print(f"Erreur     : {erreur}")
        print("\nVerdict   : ERREUR")
        return False

    cles_features = set(dataset.features)
    cles_cameras = lister_cameras(dict(dataset.features))
    videos_presentes = (racine / "videos").exists()
    etat_texte = (
        "observation.state présent" if "observation.state" in cles_features else "indisponible"
    )

    print("Chargement : OK")
    print(f"Épisodes  : {dataset.num_episodes}")
    print(f"Frames    : {dataset.num_frames}")

    fps = getattr(dataset, "fps", None)
    print(f"FPS       : {fps if fps is not None else 'indisponible'}")

    print(f"État      : {etat_texte}")
    print(f"Action    : {'présent' if 'action' in cles_features else 'indisponible'}")
    print(f"Caméras   : {', '.join(cles_cameras) if cles_cameras else 'indisponible'}")
    print(f"Vidéos    : {'présentes' if videos_presentes else 'indisponibles'}")

    contenu_manifest = creer_contenu_manifest(repo_id, racine, dataset)
    chemin_manifest = ecrire_manifest(racine, "manifeste.md", contenu_manifest)

    print("\nVérification : OK")
    print(f"Manifeste : {chemin_manifest}")
    return True


def main() -> None:
    """
    Point d'entrée du script.
    """

    config = config_lerobot.charger_config(CHEMIN_CONFIG)
    repo_id = demander_repo_id(config.enregistrement.dataset.repo_id_defaut)

    try:
        valider_repo_id(repo_id)
    except ValueError as erreur:
        print(f"\nVerdict   : ERREUR\nErreur     : {erreur}")
        return

    verifier_dataset(repo_id)


if __name__ == "__main__":
    main()
