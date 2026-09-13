import jwt
from types import SimpleNamespace

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Missing authentication token."
        )

    token = credentials.credentials.strip()

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Empty authentication token."
        )

    try:
        payload = jwt.decode(
            token,
            options={
                "verify_signature": False,
                "verify_exp": True,
            },
        )

        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Authentication token has no user ID."
            )

        # Return an object compatible with main.py:
        # current_user.id
        # current_user.email
        return SimpleNamespace(
            id=user_id,
            email=email,
            token=token,
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Authentication token has expired. Please log in again."
        )

    except jwt.InvalidTokenError as exc:
        print("JWT ERROR:", str(exc))

        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token."
        )