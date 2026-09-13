import cv2

print("OpenCV:", cv2.__version__)
print("=" * 50)

backends = [
    ("MSMF", cv2.CAP_MSMF),
    ("DSHOW", cv2.CAP_DSHOW),
    ("ANY", cv2.CAP_ANY),
]

for backend_name, backend in backends:
    print(f"\nTesting backend: {backend_name}")

    for index in range(5):
        camera = cv2.VideoCapture(index, backend)

        if not camera.isOpened():
            camera.release()
            print(f"  Camera {index}: NOT OPEN")
            continue

        ok, frame = camera.read()

        if ok and frame is not None:
            print(
                f"  Camera {index}: WORKING "
                f"{frame.shape[1]}x{frame.shape[0]}"
            )

            cv2.imshow(
                f"{backend_name} - Camera {index}",
                frame
            )

            cv2.waitKey(1000)
            cv2.destroyAllWindows()

        else:
            print(f"  Camera {index}: OPENED but READ FAILED")

        camera.release()

print("\nDiagnostic complete.")