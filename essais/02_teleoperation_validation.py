"""
Valide la téléopération minimale avec LeRobot officiel récent.

Objectif :
- connecter le bras leader ;
- connecter le bras follower ;
- lire l'action du leader ;
- envoyer cette action au follower ;
- faire une boucle courte et contrôlée ;
- déconnecter proprement les deux bras.

Ce script ne crée pas encore de dataset.
"""

import time

from lerobot.robots.so_follower.config_so_follower import SO101FollowerConfig
from lerobot.robots.so_follower.so_follower import SO101Follower
from lerobot.teleoperators.so_leader.config_so_leader import SO101LeaderConfig
from lerobot.teleoperators.so_leader.so_leader import SO101Leader


PORT_LEADER = "/dev/ttyACM0"
PORT_FOLLOWER = "/dev/ttyACM1"

ID_LEADER = "bras_leader"
ID_FOLLOWER = "bras_suiveur"

DUREE_TEST_S = 15.0
PERIODE_BOUCLE_S = 0.05


def afficher_titre(titre: str) -> None:
    """
    Affiche un titre de section lisible dans la console.
    """
    print()
    print("=" * 70)
    print(titre)
    print("=" * 70)


def creer_leader() -> SO101Leader:
    """
    Crée le bras leader avec sa configuration connue.
    """
    config = SO101LeaderConfig(
        id=ID_LEADER,
        port=PORT_LEADER,
    )

    return SO101Leader(config)


def creer_follower() -> SO101Follower:
    """
    Crée le bras follower avec sa configuration connue.

    `max_relative_target` limite les écarts de commande trop brusques. Pour ce
    premier test, on garde une limite prudente sans bloquer les mouvements normaux.
    """
    config = SO101FollowerConfig(
        id=ID_FOLLOWER,
        port=PORT_FOLLOWER,
        max_relative_target=30.0,
    )

    return SO101Follower(config)


def afficher_action(action: dict[str, float], numero_iteration: int) -> None:
    """
    Affiche périodiquement l'action lue sur le leader.

    On n'affiche pas à chaque boucle pour éviter de saturer la console.
    """
    if numero_iteration % 20 != 0:
        return

    print()
    print(f"Itération {numero_iteration}")

    for cle, valeur in action.items():
        print(f"{cle:20} : {valeur:8.2f}")


def teleoperer(leader: SO101Leader, follower: SO101Follower) -> None:
    """
    Lance une téléopération courte du follower à partir du leader.
    """
    afficher_titre("Téléopération minimale")

    instant_debut = time.monotonic()
    numero_iteration = 0

    print(f"Durée du test : {DUREE_TEST_S:.1f} s")
    print("Déplace doucement le bras leader.")
    print("Le follower devrait suivre les positions.")
    print()

    while time.monotonic() - instant_debut < DUREE_TEST_S:
        action = leader.get_action()
        follower.send_action(action)

        afficher_action(action, numero_iteration)

        numero_iteration += 1
        time.sleep(PERIODE_BOUCLE_S)


def main() -> None:
    """
    Exécute le test complet avec connexion et déconnexion propres.
    """
    leader = creer_leader()
    follower = creer_follower()

    try:
        afficher_titre("Connexion")
        print("Connexion du leader...")
        leader.connect()

        print("Connexion du follower...")
        follower.connect()

        teleoperer(leader, follower)

    finally:
        afficher_titre("Déconnexion")

        if follower.is_connected:
            print("Déconnexion du follower...")
            follower.disconnect()

        if leader.is_connected:
            print("Déconnexion du leader...")
            leader.disconnect()

        print("Fin du test.")


if __name__ == "__main__":
    main()