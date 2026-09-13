import json

import requests

from app.config import get_settings


settings = get_settings()


def available() -> bool:

    try:

        response = requests.get(
            f"{settings.ollama_base_url}/api/tags",
            timeout=2,
        )

        return response.ok

    except requests.RequestException:

        return False


def local_json(
    prompt: str,
    schema: dict | None = None,
) -> dict:

    payload = {

        "model":
            settings.ollama_model,

        "prompt":
            prompt,

        "stream":
            False,

        "format":
            schema or "json",

        "options": {
            "temperature": 0.2
        },
    }

    response = requests.post(

        f"{settings.ollama_base_url}/api/generate",

        json=payload,

        timeout=90,
    )

    response.raise_for_status()

    result = response.json()

    return json.loads(
        result["response"]
    )