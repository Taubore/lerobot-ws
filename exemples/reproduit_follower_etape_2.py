'''
Reproduire les mouvements générés par le script "Enregistre_leader.py".

Objectif:
Rejouer naïvement sur le bras suiveur LeRobot SO-101. Naïvement signifie rejouer tel quel sans correction
les mouvements enregistrés par le script "Enregistre_leader.py".

Hypothèses importantes:
- Un fichier CSV nommé "mouvement.csv" présent dans le dossier "lerobot-ws". Fichier généré par le script 
  "Enregistre_leader.py". 
- Le bras suiveur est connecté et opérationnel (calibré)
'''
from lerobot.robots.so101_follower import SO101Follower, SO101FollowerConfig
from time import sleep
import csv

PORT = "/dev/ttyACM1"
ROBOT_ID = "bras_suiveur"

DT = 0.05
FICHIER_CSV = "lerobot-ws/mouvement.csv"

JOINTS = [
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
]

robot = SO101Follower(SO101FollowerConfig(port=PORT, id=ROBOT_ID))
robot.connect()

print("\nRejouer naïvement la démonstration sur le bras follower...")

# Lecture du fichier CSV contenant les mouvements enregistrés
with open(FICHIER_CSV, newline="") as f:
    reader = csv.DictReader(f)

    # Pour chaque ligne du fichier CSV
    for row in reader:
        action = {}
        for j in JOINTS:
            action[f"{j}.pos"] = float(row[j])

        # Envoi de l'action au robot 
        robot.send_action(action)
        sleep(DT)

robot.disconnect()
print("Fin des mouvements")
