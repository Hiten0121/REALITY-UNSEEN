import base64
import getpass

import cv2
import requests
from supabase import create_client

from app.config import get_settings


settings = get_settings()

API = "http://127.0.0.1:8000"


def login_to_supabase():
    print("\n====================================")
    print("SUPABASE LOGIN")
    print("====================================")

    email = input("Email: ").strip()
    password = getpass.getpass("Password: ")

    if not email or not password:
        raise SystemExit("Email and password are required.")

    if not settings.supabase_url or not settings.supabase_key:
        raise SystemExit(
            "SUPABASE_URL or SUPABASE_KEY is missing from .env"
        )

    supabase = create_client(
        settings.supabase_url,
        settings.supabase_key,
    )

    try:
        response = supabase.auth.sign_in_with_password(
            {
                "email": email,
                "password": password,
            }
        )

    except Exception as exc:
        raise SystemExit(
            f"Supabase login failed: {exc}"
        )

    session = response.session

    if not session or not session.access_token:
        raise SystemExit(
            "Supabase login succeeded but no access token was returned."
        )

    print("Supabase login successful.")

    return session.access_token


def main():

    # ====================================
    # LOGIN
    # ====================================

    access_token = login_to_supabase()

    # ====================================
    # CAMERA
    # ====================================

    camera = cv2.VideoCapture(
        0,
        cv2.CAP_DSHOW,
    )

    if not camera.isOpened():
        raise SystemExit(
            "Camera could not be opened."
        )

    # Use the camera format that we verified works.
    camera.set(
        cv2.CAP_PROP_FOURCC,
        cv2.VideoWriter_fourcc(*"MJPG"),
    )

    camera.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        1280,
    )

    camera.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        720,
    )

    print(
        "===================================="
    )

    print(
        "REALITY: UNSEEN PIPELINE TEST"
    )

    print(
        "SPACE = scan"
    )

    print(
        "Q = quit"
    )

    print(
        "===================================="
    )

    # ====================================
    # CAMERA LOOP
    # ====================================

    while True:

        ok, frame = camera.read()

        if not ok:
            print("Camera frame read failed.")
            break

        cv2.imshow(
            "REALITY: UNSEEN",
            frame,
        )

        key = (
            cv2.waitKey(1)
            & 0xFF
        )

        if key == ord("q"):
            break

        if key == 32:

            success, encoded = cv2.imencode(
                ".jpg",
                frame,
            )

            if not success:
                print("Could not encode frame.")
                continue

            image_base64 = (
                base64.b64encode(
                    encoded.tobytes()
                )
                .decode()
            )

            payload = {
                "image_base64": image_base64,
                "mime_type": "image/jpeg",
            }

            headers = {
                "Authorization": (
                    f"Bearer {access_token}"
                )
            }

            print(
                "\nSending frame..."
            )

            try:

                response = requests.post(
                    f"{API}/api/world/analyze-frame",
                    headers=headers,
                    json=payload,
                    timeout=90,
                )

                print(
                    "HTTP:",
                    response.status_code,
                )

                try:
                    print(response.json())
                except Exception:
                    print(response.text)

            except Exception as exc:

                print(
                    "Request failed:",
                    exc,
                )

    camera.release()

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()