"""
Test minimal de connexion et de lecture du bras suiveur SO-101.

Objectif :
- vérifier que LeRobot voit correctement le bras suiveur ;
- confirmer que le port série est le bon ;
- lire une observation sans envoyer de mouvement.
"""

from time import sleep

from lerobot.robots.so101_follower import SO101Follower
from lerobot.robots.so101_follower.config_so101_follower import SO101FollowerConfig


PORT = "/dev/ttyACM1"
ID_ROBOT = "bras_suiveur"


def main() -> None:
    """
    Connecte le bras suiveur, lit quelques observations, puis déconnecte proprement.
    """
    configuration = SO101FollowerConfig(
        port=PORT,
        id=ID_ROBOT,
    )

    robot = SO101Follower(configuration)

    try:
        print(f"Connexion au bras suiveur sur {PORT}...")
        robot.connect()

        print("Connexion réussie.")
        print("Lecture des observations...")

        for numero_lecture in range(10):
            observation = robot.get_observation()

            print(f"\nObservation {numero_lecture + 1}")
            print(observation)

            sleep(0.5)

    finally:
        print("\nDéconnexion du bras suiveur...")
        robot.disconnect()
        print("Déconnexion terminée.")


if __name__ == "__main__":
    main()