"""
Officialiser un dataset LeRobot validé dans le dossier local datasets.
"""

import shutil
import subprocess
from pathlib import Path

from lerobot.datasets import LeRobotDataset

from commun import config_lerobot
from commun import utils


CHOIX_ANNULER = "1"
CHOIX_SUPPRIMER = "2"
CHOIX_AUTRE_NOM = "3"

RACINE_CACHE_LEROBOT = Path.home() / ".cache" / "huggingface" / "lerobot"
RACINE_DATASETS_OFFICIELS = Path("/home/taubore/Projets/lerobot/lerobot-ws/datasets")


def demander_repo_id_base(repo_id_defaut: str) -> str:
    """
    Demander le repo_id de base.
    """

    return utils.saisir_avec_texte_defaut("Repo_id de base : ", repo_id_defaut).strip()


def demander_nombre_lots() -> int:
    """
    Demander le nombre de lots à assembler.
    """

    texte = input("Nombre de lots : ").strip()

    if not texte.isdigit():
        raise ValueError("Le nombre de lots doit être un entier >= 0.")

    return int(texte)


def demander_repo_id_final(repo_id_defaut: str) -> str:
    """
    Demander le repo_id final officialisé.
    """

    return utils.saisir_avec_texte_defaut("Repo_id final  : ", repo_id_defaut).strip()


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


def construire_repo_ids_sources(repo_id_base: str, nombre_lots: int) -> list[str]:
    """
    Construire la liste des repo_id sources selon le nombre de lots.
    """

    if nombre_lots == 0:
        return [repo_id_base]

    if nombre_lots == 1:
        return [f"{repo_id_base}_lot01"]

    return [f"{repo_id_base}_lot{index:02d}" for index in range(1, nombre_lots + 1)]


def chemin_cache_lerobot(repo_id: str) -> Path:
    """
    Retourner le chemin cache local d'un dataset LeRobot.
    """

    return RACINE_CACHE_LEROBOT / repo_id


def chemin_dataset_officiel(repo_id: str) -> Path:
    """
    Retourner le chemin de destination officialisée.
    """

    return RACINE_DATASETS_OFFICIELS / repo_id


def gerer_destination_existante(destination: Path) -> bool:
    """
    Gérer le cas d'une destination déjà existante.
    """

    if not destination.exists():
        return True

    print("\nLe dataset final existe déjà.\n")
    print("1. Annuler")
    print("2. Supprimer et recommencer")
    print("3. Choisir un autre nom")

    choix = input("Votre choix : ").strip()

    if choix == CHOIX_ANNULER:
        return False

    if choix == CHOIX_SUPPRIMER:
        racine_resolue = RACINE_DATASETS_OFFICIELS.resolve()
        destination_resolue = destination.resolve()

        if racine_resolue not in destination_resolue.parents:
            raise ValueError("Suppression refusée : destination hors dossier datasets autorisé.")

        shutil.rmtree(destination)
        return True

    if choix == CHOIX_AUTRE_NOM:
        return False

    raise ValueError("Choix invalide.")


def copier_dataset(source: Path, destination: Path) -> None:
    """
    Copier un dataset source vers la destination officialisée.
    """

    shutil.copytree(source, destination)


def fusionner_datasets(repo_ids_sources: list[str], repo_id_final: str) -> None:
    """
    Fusionner plusieurs datasets via l'outil officiel lerobot-edit-dataset.
    """

    racines_sources = [str(chemin_cache_lerobot(repo_id)) for repo_id in repo_ids_sources]
    destination = chemin_dataset_officiel(repo_id_final)

    commande = [
        "lerobot-edit-dataset",
        "--new_repo_id",
        repo_id_final,
        "--new_root",
        str(destination),
        "--operation.type",
        "merge",
        "--operation.repo_ids",
        repr(repo_ids_sources),
        "--operation.roots",
        repr(racines_sources),
    ]

    subprocess.run(commande, check=True)


def verifier_chargement_minimal(repo_id_final: str, racine: Path) -> None:
    """
    Recharger le dataset officialisé et afficher un résumé minimal.
    """

    try:
        dataset = LeRobotDataset(repo_id=repo_id_final, root=racine)
    except Exception as erreur:  # noqa: BLE001
        print("Dataset officialisé : ERREUR")
        print(f"Erreur             : {erreur}")
        print(f"Chemin             : {racine}")
        return

    print("Dataset officialisé : OK")
    print(f"Épisodes           : {dataset.num_episodes}")
    print(f"Frames             : {dataset.num_frames}")
    print(f"Chemin             : {racine}")


def main() -> None:
    """
    Point d'entrée du script d'officialisation.
    """

    print("Officialisation du dataset LeRobot\n")

    try:
        config = config_lerobot.charger_config()
        repo_id_defaut = config.enregistrement.dataset.repo_id_defaut

        repo_id_base = demander_repo_id_base(repo_id_defaut)
        nombre_lots = demander_nombre_lots()
        repo_id_final = demander_repo_id_final(repo_id_defaut)

        valider_repo_id(repo_id_base)
        valider_repo_id(repo_id_final)

        repo_ids_sources = construire_repo_ids_sources(repo_id_base, nombre_lots)
        destination = chemin_dataset_officiel(repo_id_final)

        print("\nSources :")
        for source in repo_ids_sources:
            print(f"- {source}")

        print("\nFinal :")
        print(f"- {repo_id_final}")

        print("\nDestination :")
        print(destination)
        confirmation = input("\nEntrée = continuer, q = annuler : ").strip().lower()

        if confirmation == "q":
            print("Opération annulée.")
            return

        if not gerer_destination_existante(destination):
            print("Opération annulée.")
            return

        destination.parent.mkdir(parents=True, exist_ok=True)

        if len(repo_ids_sources) == 1:
            source = chemin_cache_lerobot(repo_ids_sources[0])
            if not source.exists():
                raise FileNotFoundError(f"Source introuvable : {source}")
            copier_dataset(source, destination)
        else:
            for repo_id_source in repo_ids_sources:
                source = chemin_cache_lerobot(repo_id_source)
                if not source.exists():
                    raise FileNotFoundError(f"Source introuvable : {source}")
            fusionner_datasets(repo_ids_sources, repo_id_final)

        verifier_chargement_minimal(repo_id_final, destination)

    except (ValueError, FileNotFoundError, subprocess.CalledProcessError) as erreur:
        print(f"Erreur : {erreur}")


if __name__ == "__main__":
    main()
