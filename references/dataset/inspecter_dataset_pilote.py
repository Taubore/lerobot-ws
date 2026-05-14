"""
Inspecter le dataset pilote LeRobot.

Objectif :
Faire une inspection minimale et factuelle du dataset LeRobot. Vérifier que le dataset est lisible,
qu’il contient bien le nombre attendu d’épisodes, que le nombre total de frames et le FPS sont
cohérents avec la durée enregistrée et que les champs essentiels sont présents, notamment :
    - observations caméra
    - état du robot
    - actions
    - informations d’épisode.

Le script affiche aussi les dimensions ou types des données principales afin de confirmer que les
observations et actions ne sont pas vides ou incohérentes. Son rôle est de décider si le dataset
est techniquement assez sain pour passer à un premier entraînement, ou s’il faut corriger
l’enregistrement avant d’aller plus loin.
"""

import os
from pathlib import Path
from typing import Any, cast

from lerobot.datasets import LeRobotDataset


FPS = 30
NB_EPISODES_ATTENDUS = 10
DUREE_EPISODE_ATTENDUE_S = 10
ECART_DUREE_ACCEPTE_S = 1.0

EMPLACEMENT_PROJET = Path("/home/taubore/Projets/lerobot/lerobot-ws")
EMPLACEMENT_DATASETS = EMPLACEMENT_PROJET / "datasets"

REPO_DATASET = "taubore/deplacer_cube_v03"
EMPLACEMENT_DATASET = EMPLACEMENT_DATASETS / REPO_DATASET

CHAMPS_ESSENTIELS = (
    "observation.state",
    "action",
    "timestamp",
    "frame_index",
    "episode_index",
    "task_index",
)


def _inspecter_structure_base(ds: LeRobotDataset) -> None:
    """
    Afficher les informations générales de la structure de base du dataset.
    """

    print(f"Dataset  : {REPO_DATASET}")
    print(f"Chemin   : {EMPLACEMENT_DATASET}")
    _afficher_statut("FPS      :", ds.fps == FPS, f"{ds.fps} / {FPS}")
    _afficher_statut(
        "Épisodes :",
        ds.num_episodes == NB_EPISODES_ATTENDUS,
        f"{ds.num_episodes} / {NB_EPISODES_ATTENDUS}",
    )

    print("================================================================================")


def _inspecter_episodes(ds: LeRobotDataset) -> None:
    """
    Afficher la durée approximative de chaque épisode et vérifier la cohérence
    avec les informations globales du dataset.
    """

    episodes: dict[int, int] = {}

    for index_frame in range(ds.num_frames):
        item = ds.get_raw_item(index_frame)
        episode = int(item["episode_index"])
        episodes[episode] = episodes.get(episode, 0) + 1

    nb_frames_cumulees = sum(episodes.values())
    duree_totale_s = ds.num_frames / ds.fps
    duree_attendue_s = ds.num_episodes * DUREE_EPISODE_ATTENDUE_S

    print("Résumé par épisode :")
    _afficher_statut(
        "Épisodes reconstruits :",
        len(episodes) == ds.num_episodes,
        f"{len(episodes)} / {ds.num_episodes}",
    )
    _afficher_statut(
        "Frames cumulées :",
        nb_frames_cumulees == ds.num_frames,
        f"{nb_frames_cumulees} / {ds.num_frames}",
    )
    _afficher_statut(
        "Durée totale :",
        abs(duree_totale_s - duree_attendue_s) <= ECART_DUREE_ACCEPTE_S,
        f"{duree_totale_s:.2f} s / {duree_attendue_s:.2f} s",
    )
    print()

    for episode, nb_frames in sorted(episodes.items()):
        duree_s = nb_frames / ds.fps
        ecart_s = abs(duree_s - DUREE_EPISODE_ATTENDUE_S)

        _afficher_statut(
            f"Épisode {episode:02d} :",
            ecart_s <= ECART_DUREE_ACCEPTE_S,
            f"{nb_frames} frames, {duree_s:.2f} s",
        )

    print("================================================================================")


def _inspecter_champs(ds: LeRobotDataset) -> None:
    """
    Vérifier la présence des champs essentiels du dataset.
    """

    cles_features = set(ds.features)
    cles_camera = sorted(cle for cle in cles_features if cle.startswith("observation.images."))

    print("Champs essentiels :")

    for cle in CHAMPS_ESSENTIELS:
        _afficher_statut(cle, cle in cles_features)

    _afficher_statut(
        "observations caméra :",
        bool(cles_camera),
        ", ".join(cles_camera) or "absent",
    )
    print("================================================================================")


def _inspecter_donnees_principales(ds: LeRobotDataset) -> None:
    """
    Afficher les dimensions ou types des données principales.
    """

    if ds.num_frames == 0:
        print("Aucune frame à inspecter.")
        print("================================================================================")
        return

    item = ds[0]
    cles_camera = sorted(cle for cle in ds.features if cle.startswith("observation.images."))
    cles_a_decrire = [*cles_camera, "observation.state", "action", "episode_index"]

    print("Données principales sur la première frame :")

    for cle in cles_a_decrire:
        _decrire_champ(ds, item, cle)

    print("================================================================================")


def _decrire_champ(ds: LeRobotDataset, item: dict[str, Any], cle: str) -> None:
    """
    Afficher une description lisible d'un champ.
    """

    feature = ds.features.get(cle)
    valeur = item.get(cle)

    print(f"{cle} :")

    if feature is None:
        print("  Statut : ATTENTION")
        print("  Feature: absente")
        print()
        return

    if valeur is None:
        print("  Statut : ATTENTION")
        print("  Valeur : absente de la frame")
        print()
        return

    forme_feature = feature.get("shape")
    dtype_feature = feature.get("dtype")
    forme_valeur = getattr(valeur, "shape", None)
    dtype_valeur = getattr(valeur, "dtype", None)
    statut = "OK" if _valeur_non_vide(valeur) else "ATTENTION"

    print(f"  Statut : {statut}")
    print(f"  Feature: dtype={dtype_feature}, forme={forme_feature}")
    print(f"  Valeur : type={type(valeur).__name__}")

    if forme_valeur is not None:
        print(f"           forme={tuple(forme_valeur)}")

    if dtype_valeur is not None:
        print(f"           dtype={dtype_valeur}")

    print()


def _valeur_non_vide(valeur: Any) -> bool:
    """
    Déterminer si une valeur lue dans le dataset semble non vide.
    """

    nombre_elements = getattr(valeur, "numel", None)

    if callable(nombre_elements):
        return cast(int, nombre_elements()) > 0

    taille = getattr(valeur, "size", None)

    if isinstance(taille, int):
        return taille > 0

    if hasattr(valeur, "__len__") and not isinstance(valeur, str):
        return len(valeur) > 0

    return valeur is not None


def _afficher_statut(libelle: str, condition: bool, detail: str = "") -> None:
    """
    Afficher un statut simple et lisible.
    """

    statut = "OK" if condition else "ATTENTION"
    valeur = f"{detail}" if detail else ""

    print(f"{libelle} {valeur} ({statut})")


def executer() -> None:
    """
    Amorce du script.
    """

    dataset = LeRobotDataset(
        repo_id=REPO_DATASET,
        root=EMPLACEMENT_DATASET,
    )

    os.system("clear")
    print("================================================================================")
    print("Inspection d'un dataset 'LeRobotDataset'")
    print("================================================================================")
    _inspecter_structure_base(dataset)
    _inspecter_episodes(dataset)
    _inspecter_champs(dataset)
    _inspecter_donnees_principales(dataset)


if __name__ == "__main__":
    executer()
