import cv2

camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not camera.isOpened():
    print("Camera could not be opened.")
    raise SystemExit

print("Camera opened.")

for i in range(30):
    ok, frame = camera.read()

    if not ok or frame is None:
        print("Frame read failed")
        continue

    print(
        f"Frame {i}: "
        f"shape={frame.shape}, "
        f"min={frame.min()}, "
        f"max={frame.max()}, "
        f"mean={frame.mean():.2f}"
    )

    cv2.imshow("Camera Test", frame)

    if cv2.waitKey(100) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()