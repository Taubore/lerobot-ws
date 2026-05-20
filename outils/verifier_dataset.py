"""
Vérifier minimalement un dataset brut LeRobot sans rien modifier.
"""

from pathlib import Path

from lerobot.datasets import LeRobotDataset


RACINE_CACHE_LEROBOT = Path.home() / ".cache" / "huggingface" / "lerobot"
PREFIXE_CAMERA = "observation.images."


def demander_repo_id() -> str:
    """
    Demander le repo_id à vérifier.
    """

    return input("Repo_id du dataset à vérifier : ").strip()


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


def verifier_dataset(repo_id: str) -> bool:
    """
    Charger le dataset et afficher une vérification courte.
    """

    print("\nVérification du dataset LeRobot\n")
    print(f"Dataset : {repo_id}\n")

    racine = RACINE_CACHE_LEROBOT / repo_id

    try:
        dataset = LeRobotDataset(repo_id=repo_id, root=racine)
    except Exception as erreur:  # noqa: BLE001
        print("Chargement : ERREUR")
        print(f"Erreur     : {erreur}")
        print("\nVerdict   : ERREUR")
        return False

    cles_features = set(dataset.features)
    cles_cameras = sorted(cle for cle in cles_features if cle.startswith(PREFIXE_CAMERA))
    videos_presentes = (racine / "videos").exists()

    print("Chargement : OK")
    print(f"Épisodes  : {dataset.num_episodes}")
    print(f"Frames    : {dataset.num_frames}")

    fps = getattr(dataset, "fps", None)
    print(f"FPS       : {fps if fps is not None else 'indisponible'}")

    print(
        "État      : "
        f"{'observation.state présent' if 'observation.state' in cles_features else 'indisponible'}"
    )
    print(f"Action    : {'présent' if 'action' in cles_features else 'indisponible'}")
    print(f"Caméras   : {', '.join(cles_cameras) if cles_cameras else 'indisponible'}")
    print(f"Vidéos    : {'présentes' if videos_presentes else 'indisponibles'}")

    print("\nVerdict   : OK")
    return True


def main() -> None:
    """
    Point d'entrée du script.
    """

    repo_id = demander_repo_id()

    try:
        valider_repo_id(repo_id)
    except ValueError as erreur:
        print(f"\nVerdict   : ERREUR\nErreur     : {erreur}")
        return

    verifier_dataset(repo_id)


if __name__ == "__main__":
    main()
