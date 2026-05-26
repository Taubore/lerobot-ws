"""
Tester minimalement la RealSense globale et l'Arducam de pince ensemble.
"""

from pathlib import Path

from lerobot.cameras import ColorMode, Cv2Rotation
from lerobot.cameras.opencv import OpenCVCamera, OpenCVCameraConfig
from lerobot.cameras.realsense import RealSenseCamera, RealSenseCameraConfig


SERIAL_REALSENSE = "310522072905"
ID_CAMERA_PINCE = Path("/dev/video8")


def main() -> None:
    """
    Lire une image sur chaque caméra, puis fermer proprement.
    """

    config_globale = RealSenseCameraConfig(
        serial_number_or_name=SERIAL_REALSENSE,
        fps=15,
        width=640,
        height=480,
        color_mode=ColorMode.RGB,
        use_depth=False,
        rotation=Cv2Rotation.NO_ROTATION,
        warmup_s=3,
    )

    config_pince = OpenCVCameraConfig(
        index_or_path=ID_CAMERA_PINCE,
        fps=30,
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

        image_globale = camera_globale.read()
        image_pince = camera_pince.read()

        print(f"Image globale RealSense : {image_globale.shape}")
        print(f"Image pince Arducam     : {image_pince.shape}")

    finally:
        camera_pince.disconnect()
        camera_globale.disconnect()


if __name__ == "__main__":
    main()