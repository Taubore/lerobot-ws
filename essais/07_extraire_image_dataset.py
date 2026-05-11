"""
Extraire une image du dataset pilote LeRobot.

Objectif :
Sauvegarder une image caméra provenant d'une frame précise du dataset afin de
voir exactement ce que le modèle reçoit comme observation visuelle.
"""

from pathlib import Path

from PIL import Image
from lerobot.datasets import LeRobotDataset


EMPLACEMENT_PROJET = Path("/home/taubore/Projets/lerobot/lerobot-ws")
EMPLACEMENT_DATASETS = EMPLACEMENT_PROJET / "datasets"
EMPLACEMENT_CAPTURES = EMPLACEMENT_PROJET / "captures"

REPO_DATASET = "taubore/so101_cube_vers_carre_pilote"
EMPLACEMENT_DATASET = EMPLACEMENT_DATASETS / REPO_DATASET

EPISODE_A_EXTRAIRE = 0
TEMPS_A_EXTRAIRE_S = 5.0

CLE_IMAGE = "observation.images.globale"


def trouver_index_frame_par_temps(
    dataset: LeRobotDataset,
    episode: int,
    temps_s: float,
) -> int:
    """
    Trouver l'index global de la frame la plus proche d'un temps donné.

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


def extraire_image() -> None:
    """
    Extraire l'image caméra d'une frame et l'enregistrer en PNG.
    """

    dataset = LeRobotDataset(
        repo_id=REPO_DATASET,
        root=EMPLACEMENT_DATASET,
    )

    index_frame = trouver_index_frame_par_temps(
        dataset=dataset,
        episode=EPISODE_A_EXTRAIRE,
        temps_s=TEMPS_A_EXTRAIRE_S,
    )

    item = dataset[index_frame]
    image_tensor = item[CLE_IMAGE]

    # Le tenseur LeRobot/PyTorch est au format [canaux, hauteur, largeur].
    # Pillow attend plutôt [hauteur, largeur, canaux].
    image_uint8 = (
        image_tensor
        .clamp(0.0, 1.0)
        .mul(255)
        .byte()
        .permute(1, 2, 0)
        .cpu()
        .numpy()
    )

    image = Image.fromarray(image_uint8)

    EMPLACEMENT_CAPTURES.mkdir(exist_ok=True)

    nom_fichier = (
        f"frame_episode_{EPISODE_A_EXTRAIRE:02d}"
        f"_t_{TEMPS_A_EXTRAIRE_S:05.2f}.png"
    )
    emplacement_image = EMPLACEMENT_CAPTURES / nom_fichier

    image.save(emplacement_image)

    print(f"Image extraite : {emplacement_image}")
    print(f"Épisode        : {EPISODE_A_EXTRAIRE}")
    print(f"Temps demandé  : {TEMPS_A_EXTRAIRE_S:.2f} s")
    print(f"Frame globale  : {index_frame}")


if __name__ == "__main__":
    extraire_image()