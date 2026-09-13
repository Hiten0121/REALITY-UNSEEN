from supabase import Client, create_client

from app.config import get_settings


settings = get_settings()


def get_supabase(
    access_token: str | None = None,
) -> Client:

    if not settings.supabase_url:
        raise RuntimeError(
            "SUPABASE_URL is missing from .env"
        )

    if not settings.supabase_key:
        raise RuntimeError(
            "SUPABASE_KEY is missing from .env"
        )

    client = create_client(
        settings.supabase_url,
        settings.supabase_key,
    )

    if access_token:
        client.postgrest.auth(access_token)

    return client