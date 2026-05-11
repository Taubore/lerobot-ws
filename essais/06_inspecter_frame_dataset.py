"""
Inspecter une frame du dataset pilote LeRobot.

Objectif :
Afficher le contenu principal d'une frame pour comprendre ce que le modèle
recevra pendant l'entraînement.
"""

from pathlib import Path
from typing import Any

from lerobot.datasets import LeRobotDataset


EMPLACEMENT_PROJET = Path("/home/taubore/Projets/lerobot/lerobot-ws")
EMPLACEMENT_DATASETS = EMPLACEMENT_PROJET / "datasets"

REPO_DATASET = "taubore/so101_cube_vers_carre_pilote"
EMPLACEMENT_DATASET = EMPLACEMENT_DATASETS / REPO_DATASET

EPISODE_A_INSPECTER = 0
TEMPS_A_INSPECTER_S = 5.0


def decrire_valeur(nom: str, valeur: Any) -> None:
    """
    Afficher une description courte d'une valeur du dataset.

    Les valeurs peuvent être des tenseurs, des nombres, des chaînes ou d'autres
    objets selon la colonne inspectée.
    """

    type_valeur = type(valeur).__name__
    forme = getattr(valeur, "shape", None)
    dtype = getattr(valeur, "dtype", None)

    print(f"{nom}")
    print(f"  type  : {type_valeur}")

    if forme is not None:
        print(f"  forme : {forme}")

    if dtype is not None:
        print(f"  dtype : {dtype}")

    if isinstance(valeur, int | float | str):
        print(f"  valeur: {valeur}")

    print()


def trouver_index_frame_par_temps(
    dataset: LeRobotDataset,
    episode: int,
    temps_s: float,
) -> int:
    """
    Trouver l'index global de la frame la plus proche d'un temps donné
    dans un épisode.

    Le temps demandé est exprimé en secondes depuis le début de l'épisode.
    """

    meilleur_index = -1
    meilleur_ecart = float("inf")

    for index_frame in range(dataset.num_frames):
        item_brut = dataset.get_raw_item(index_frame)

        if int(item_brut["episode_index"]) != episode:
            continue

        timestamp = float(item_brut["timestamp"])
        ecart = abs(timestamp - temps_s)

        if ecart < meilleur_ecart:
            meilleur_index = index_frame
            meilleur_ecart = ecart

    if meilleur_index == -1:
        raise ValueError(f"Épisode introuvable : {episode}")

    return meilleur_index


def inspecter_frame() -> None:
    """
    Inspecter la première frame de l'épisode demandé.
    """

    dataset = LeRobotDataset(
        repo_id=REPO_DATASET,
        root=EMPLACEMENT_DATASET,
    )

    index_frame = trouver_index_frame_par_temps(
        dataset=dataset,
        episode=EPISODE_A_INSPECTER,
        temps_s=TEMPS_A_INSPECTER_S,
    )
    item = dataset[index_frame]

    print(f"Dataset : {REPO_DATASET}")
    print(f"Épisode : {EPISODE_A_INSPECTER}")
    print(f"Temps   : {TEMPS_A_INSPECTER_S:.2f} s")
    print(f"Frame   : {index_frame}")
    print()

    cles_importantes = [
        "observation.images.globale",
        "observation.state",
        "action",
        "timestamp",
        "frame_index",
        "episode_index",
        "task_index",
    ]

    for cle in cles_importantes:
        if cle in item:
            decrire_valeur(cle, item[cle])
        else:
            print(f"{cle}")
            print("  absent")
            print()
    
    afficher_vecteur_nommee(dataset, item, "observation.state")
    afficher_vecteur_nommee(dataset, item, "action")


def afficher_vecteur_nommee(dataset: LeRobotDataset, item: dict[str, Any], cle: str) -> None:
    """
    Afficher un vecteur du dataset avec les noms internes de ses composantes.

    Exemple :
    - `observation.state`
    - `action`

    LeRobot conserve normalement les noms des composantes dans `dataset.features`.
    Cela permet de relier les nombres aux articulations ou servos du robot.
    """

    valeur = item[cle]
    valeurs = valeur.tolist()

    feature: dict[str, Any] = dataset.features[cle]
    noms: list[str] = feature.get("names", [])

    print(f"{cle} détaillé :")

    if not noms:
        print("  Aucun nom interne trouvé.")
        print(f"  valeurs: {valeurs}")
        print()
        return

    for nom, nombre in zip(noms, valeurs, strict=True):
        print(f"  {nom}: {nombre:.4f}")

    print()


if __name__ == "__main__":
    inspecter_frame()