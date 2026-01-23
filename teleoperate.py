
'''
Téléopération d'un bras LeRobot follower SO-101 à partir d'un leader SO-101

Objectif:
Reporduire en temps réel les mouvements effectués sur un bras leader SO-101 par un bras follower SO-101. On vise un code 
très simple et didactique. Donc pas de correction des mouvements, ni de filtrage, ni de gestion des erreurs.

Hypothèses importantes:
- Le bras leader est connecté et opérationnel (calibré)
- Le bras suiveur est connecté et opérationnel (calibré)
'''
from lerobot.teleoperators.so101_leader import SO101LeaderConfig, SO101Leader
from lerobot.robots.so101_follower import SO101FollowerConfig, SO101Follower

robot_config = SO101FollowerConfig(
    port="/dev/ttyACM1",
    id="bras_suiveur",
)

teleop_config = SO101LeaderConfig(
    port="/dev/ttyACM0",
    id="bras_leader",
)

robot = SO101Follower(robot_config)
teleop_device = SO101Leader(teleop_config)
robot.connect()
teleop_device.connect()

while True:
    action = teleop_device.get_action()
    robot.send_action(action)