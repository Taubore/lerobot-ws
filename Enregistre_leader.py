from lerobot.teleoperators.so101_leader import SO101Leader, SO101LeaderConfig
from time import sleep
import csv

PORT = "/dev/ttyACM0"                     # Port du bras leader - AJUSTER SELON VOTRE CONFIG.
ROBOT_ID = "bras_leader"                  # Identifiant du bras leader - AJUSTER SELON VOTRE CONFIG.
DT = 0.05                                 # 20 Hz (1 / 0.05)
DURATION = 20.0                           # Durée d'enregistrement (secondes)
FICHIER_CSV = "lerobot_ws/mouvement.csv"  # Fichier de sauvegarde des mouvements - AJUSTER LE DOSSIER SELON VOTRE CONFIG.

JOINTS = [
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
]

# Connexion au bras leader
robot = SO101Leader(SO101LeaderConfig(port=PORT, id=ROBOT_ID))
robot.connect()

print(f"\nEnregistrement des mouvement du bras leader : {DURATION} secondes à {1/DT:.0f} Hz")
for i in range(10, 0, -1):
    print(f"Début de l'enregistrement dans {i} secondes...", end="\r", flush=True)
    sleep(1)

nb = int(DURATION / DT)

with open(FICHIER_CSV, mode="w", newline="") as f:
    writer = csv.writer(f)

    # En-tête
    writer.writerow(["t"] + JOINTS)

    for i in range(nb + 1):
        t = i * DT
        print(f"Bouger le bras leader. {t:.2f} secondes restantes...", end="\r", flush=True)
        action = robot.get_action()

        row = [f"{t:.2f}"]
        for j in JOINTS:
            row.append(f"{float(action[f'{j}.pos']):.2f}")

        writer.writerow(row)
        sleep(DT)

robot.disconnect()
print(f"Fin de l'enregistrement. Les mouvements sont conservés dans le fichier : {FICHIER_CSV}")
