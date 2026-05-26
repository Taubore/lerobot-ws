"""
Visualiser en direct la RealSense globale et l'Arducam de pince avec Rerun.
"""

import time

import rerun as rr

from pathlib import Path

from lerobot.cameras import ColorMode, Cv2Rotation
from lerobot.cameras.opencv import OpenCVCamera, OpenCVCameraConfig
from lerobot.cameras.realsense import RealSenseCamera, RealSenseCameraConfig


SERIAL_REALSENSE = "310522072905"
ID_CAMERA_PINCE = Path("/dev/video8")

FPS_GLOBALE = 15
FPS_PINCE = 30


def main() -> None:
    """
    Afficher les deux caméras dans Rerun pour ajuster cadrage et focus.
    """

    rr.init("controle_cameras_lerobot", spawn=True)

    config_globale = RealSenseCameraConfig(
        serial_number_or_name=SERIAL_REALSENSE,
        fps=FPS_GLOBALE,
        width=640,
        height=480,
        color_mode=ColorMode.RGB,
        use_depth=False,
        rotation=Cv2Rotation.NO_ROTATION,
        warmup_s=3,
    )

    config_pince = OpenCVCameraConfig(
        index_or_path=ID_CAMERA_PINCE,
        fps=FPS_PINCE,
        width=640,
        height=480,
        color_mode=ColorMode.RGB,
        rotation=Cv2Rotation.NO_ROTATION,
    )

    camera_globale = RealSenseCamera(config_globale)
    camera_pince = OpenCVCamera(config_pince)

    try:
        camera_globale.connect()
        camera_pince.connect()

        print("Visualisation Rerun active.")
        print("Ajuster le cadrage et le focus, puis arrêter avec Ctrl+C.")

        while True:
            image_globale = camera_globale.read()
            image_pince = camera_pince.read()

            rr.log("cameras/globale", rr.Image(image_globale))
            rr.log("cameras/pince", rr.Image(image_pince))

            time.sleep(1 / FPS_GLOBALE)

    except KeyboardInterrupt:
        print("\nArrêt demandé.")

    finally:
        camera_pince.disconnect()
        camera_globale.disconnect()
        print("Caméras déconnectées.")


if __name__ == "__main__":
    main()