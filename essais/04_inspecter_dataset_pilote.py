"""
Inspecter le dataset pilote LeRobot enregistré localement.

Objectif :
Vérifier rapidement que le dataset existe, qu'il contient les épisodes attendus
et que les observations/actions principales sont présentes.
"""

from pathlib import Path

from lerobot.datasets import LeRobotDataset


RACINE_PROJET = Path("/home/taubore/Projets/lerobot/lerobot-ws")
RACINE_DATASETS = RACINE_PROJET / "datasets"

REPO_DATASET = "taubore/so101_cube_vers_carre_pilote"
CHEMIN_DATASET = RACINE_DATASETS / REPO_DATASET


def inspecter_dataset() -> None:
    """
    Afficher les informations essentielles du dataset pilote.
    """

    dataset = LeRobotDataset(
        repo_id=REPO_DATASET,
        root=CHEMIN_DATASET,
    )

    print(f"Dataset : {REPO_DATASET}")
    print(f"Chemin  : {CHEMIN_DATASET}")
    print(f"FPS     : {dataset.fps}")
    print(f"Épisodes: {dataset.num_episodes}")
    print(f"Frames  : {dataset.num_frames}")
    print()

    print("Features :")
    for nom_feature in dataset.features:
        print(f"- {nom_feature}")


if __name__ == "__main__":
    inspecter_dataset()