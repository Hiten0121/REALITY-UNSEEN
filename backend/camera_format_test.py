import cv2
import time

formats = [
    ("MJPG", cv2.VideoWriter_fourcc(*"MJPG")),
    ("YUY2", cv2.VideoWriter_fourcc(*"YUY2")),
    ("H264", cv2.VideoWriter_fourcc(*"H264")),
]

resolutions = [
    (640, 480),
    (1280, 720),
]

for format_name, fourcc in formats:
    for width, height in resolutions:

        print("\n" + "=" * 50)
        print(f"Testing {format_name} {width}x{height}")

        camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        if not camera.isOpened():
            print("Could not open camera")
            camera.release()
            continue

        camera.set(cv2.CAP_PROP_FOURCC, fourcc)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        time.sleep(1)

        ok, frame = camera.read()

        if not ok or frame is None:
            print("READ FAILED")
            camera.release()
            continue

        print("Actual resolution:", frame.shape)
        print("Min:", frame.min())
        print("Max:", frame.max())
        print("Mean brightness:", frame.mean())

        cv2.imshow(
            f"{format_name} {width}x{height}",
            frame
        )

        cv2.waitKey(1500)
        cv2.destroyAllWindows()

        camera.release()

print("\nFinished.")