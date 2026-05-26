"""
Tester minimalement la RealSense D435IF avec LeRobot.
"""

from lerobot.cameras import ColorMode, Cv2Rotation
from lerobot.cameras.realsense import RealSenseCamera, RealSenseCameraConfig


SERIAL_REALSENSE = "310522072905"


def main() -> None:
    """
    Lire une seule image RGB avec la RealSense.
    """

    config = RealSenseCameraConfig(
        serial_number_or_name=SERIAL_REALSENSE,
        fps=15,
        width=640,
        height=480,
        color_mode=ColorMode.RGB,
        use_depth=False,
        rotation=Cv2Rotation.NO_ROTATION,
        warmup_s=3,
    )

    camera = RealSenseCamera(config)

    try:
        camera.connect()
        image = camera.read()
        print(f"Image RGB RealSense : {image.shape}")
    finally:
        camera.disconnect()


if __name__ == "__main__":
    main()