"""
Vérifier si PyTorch voit le GPU NVIDIA.

Objectif :
Confirmer que l'environnement Python actif peut utiliser CUDA pour entraîner
une politique LeRobot localement.
"""

import torch


def verifier_gpu() -> None:
    """
    Afficher l'état CUDA/PyTorch utile avant un entraînement local.
    """

    print(f"Version PyTorch : {torch.__version__}")
    print(f"CUDA disponible : {torch.cuda.is_available()}")

    if not torch.cuda.is_available():
        print()
        print("Résultat : CUDA n'est pas disponible dans cet environnement.")
        print("On pourra entraîner sur CPU, mais ce sera beaucoup plus lent.")
        return

    nb_gpus = torch.cuda.device_count()
    index_gpu = torch.cuda.current_device()
    nom_gpu = torch.cuda.get_device_name(index_gpu)

    print(f"Nombre de GPU   : {nb_gpus}")
    print(f"GPU actif       : {index_gpu}")
    print(f"Nom du GPU      : {nom_gpu}")

    tenseur = torch.tensor([1.0, 2.0, 3.0], device="cuda")
    print(f"Test tenseur    : {tenseur}")
    print()
    print("Résultat : CUDA fonctionne avec PyTorch.")


if __name__ == "__main__":
    verifier_gpu()