"""
Tester minimalement la caméra de pince Arducam avec LeRobot.
"""

from pathlib import Path

from lerobot.cameras import ColorMode, Cv2Rotation
from lerobot.cameras.opencv import OpenCVCamera, OpenCVCameraConfig


ID_CAMERA_PINCE = Path("/dev/video8")


def main() -> None:
    """
    Lire une seule image RGB avec la caméra de pince.
    """

    config = OpenCVCameraConfig(
        index_or_path=ID_CAMERA_PINCE,
        fps=30,
        width=640,
        height=480,
        color_mode=ColorMode.RGB,
        rotation=Cv2Rotation.NO_ROTATION,
    )

    camera = OpenCVCamera(config)

    try:
        camera.connect()
        image = camera.read()
        print(f"Image RGB caméra de pince : {image.shape}")
    finally:
        camera.disconnect()


if __name__ == "__main__":
    main()
