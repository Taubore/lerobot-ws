
'''
Téléopération d'un bras LeRobot follower SO-101 à partir d'un leader SO-101

Objectif:
Reproduire en temps réel les mouvements effectués sur un bras leader SO-101 par un bras follower 
SO-101. On vise un code très simple et didactique. Donc pas de correction des mouvements, ni de 
filtrage, ni de gestion des erreurs. Utile pour pratiquer un mouvement avant de produire 
des enregistrements de datasets.

Hypothèses importantes:
- Le bras leader est connecté et opérationnel (calibré)
- Le bras suiveur est connecté et opérationnel (calibré)
'''
from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig
from lerobot.teleoperators.so_leader import SO101Leader, SO101LeaderConfig


PORT_LEADER = "/dev/ttyACM0"
PORT_FOLLOWER = "/dev/ttyACM1"

ID_LEADER = "bras_leader"
ID_FOLLOWER = "bras_suiveur"


robot_config = SO101FollowerConfig(
    port=PORT_FOLLOWER,
    id=ID_FOLLOWER,
)

teleop_config = SO101LeaderConfig(
    port=PORT_LEADER,
    id=ID_LEADER,
)

robot = SO101Follower(robot_config)
teleop = SO101Leader(teleop_config)

try:
    robot.connect()
    teleop.connect()

    while True:
        action = teleop.get_action()
        robot.send_action(action)

except KeyboardInterrupt:
    pass

finally:
    teleop.disconnect()
    robot.disconnect()