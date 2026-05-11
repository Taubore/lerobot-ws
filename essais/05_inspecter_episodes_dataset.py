"""
Inspecter les épisodes du dataset pilote LeRobot.

Objectif :
Afficher un résumé par épisode pour confirmer que les épisodes sont bien
séparés dans les métadonnées, même si la vidéo est regroupée dans un seul MP4.
"""

from pathlib import Path

from lerobot.datasets import LeRobotDataset


FPS = 30

EMPLACEMENT_PROJET = Path("/home/taubore/Projets/lerobot/lerobot-ws")
EMPLACEMENT_DATASETS = EMPLACEMENT_PROJET / "datasets"

REPO_DATASET = "taubore/so101_cube_vers_carre_pilote"
EMPLACEMENT_DATASET = EMPLACEMENT_DATASETS / REPO_DATASET


def inspecter_episodes() -> None:
    """
    Afficher le nombre de frames et la durée approximative de chaque épisode.
    """

    dataset = LeRobotDataset(
        repo_id=REPO_DATASET,
        root=EMPLACEMENT_DATASET,
    )

    print(f"Dataset : {REPO_DATASET}")
    print(f"Chemin  : {EMPLACEMENT_DATASET}")
    print(f"FPS     : {dataset.fps}")
    print(f"Épisodes: {dataset.num_episodes}")
    print(f"Frames  : {dataset.num_frames}")
    print()

    episodes: dict[int, int] = {}

    for index_frame in range(dataset.num_frames):
        item = dataset.get_raw_item(index_frame)
        episode = int(item["episode_index"])
        episodes[episode] = episodes.get(episode, 0) + 1

    print("Résumé par épisode :")

    for episode, nb_frames in sorted(episodes.items()):
        duree_s = nb_frames / dataset.fps

        print(
            f"- Épisode {episode:02d} : "
            f"{nb_frames:4d} frames, "
            f"{duree_s:5.2f} s"
        )


if __name__ == "__main__":
    inspecter_episodes()