from lerobot.robots.so101_follower import SO101Follower, SO101FollowerConfig
from time import sleep
import csv

PORT = "/dev/ttyACM1"
ROBOT_ID = "bras_suiveur"

DT = 0.05
FICHIER_CSV = "lerobot_ws/mouvement.csv"

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

with open(FICHIER_CSV, newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        action = {}
        for j in JOINTS:
            action[f"{j}.pos"] = float(row[j])

        robot.send_action(action)
        sleep(DT)

robot.disconnect()
print("Fin des mouvements")
