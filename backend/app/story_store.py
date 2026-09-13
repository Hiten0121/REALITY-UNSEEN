from datetime import datetime, timezone
import json

from app.db import get_supabase
from app.schemas import (
    StoryState,
    StoryVersion,
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_story(
    story: StoryState,
    user_id: str,
    access_token: str,
):
    """
    Create a new canonical story owned by a user.
    The user's JWT is forwarded to Supabase so RLS can evaluate auth.uid().
    """

    supabase = get_supabase(access_token)

    data = {
        "id": story.story_id,
        "user_id": user_id,
        "title": story.title,
        "summary": story.premise,
        "state_json": story.model_dump(),
        "history_json": [],
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }

    response = (
        supabase
        .table("stories")
        .insert(data)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Failed to create story in Supabase."
        )

    return response.data[0]


def save_story(
    story: StoryState,
    versions: list[StoryVersion],
    user_id: str,
    access_token: str,
):
    """
    Save the current canonical story and its history.
    """

    supabase = get_supabase(access_token)

    data = {
        "id": story.story_id,
        "user_id": user_id,
        "title": story.title,
        "summary": story.premise,
        "state_json": story.model_dump(),
        "history_json": [
            version.model_dump()
            for version in versions
        ],
        "updated_at": now_iso(),
    }

    response = (
        supabase
        .table("stories")
        .upsert(
            data,
            on_conflict="id",
        )
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Failed to save story in Supabase."
        )

    return response.data[0]


def get_story(
    story_id: str,
    user_id: str,
    access_token: str,
):
    """
    Get a story only if it belongs to this user.
    """

    supabase = get_supabase(access_token)

    response = (
        supabase
        .table("stories")
        .select("*")
        .eq("id", story_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def parse_record(record: dict):

    if not record:
        return None, []

    state_json = record.get(
        "state_json",
        {},
    )

    history_json = record.get(
        "history_json",
        [],
    )

    if isinstance(state_json, str):
        state_json = json.loads(state_json)

    if isinstance(history_json, str):
        history_json = json.loads(history_json)

    story = StoryState.model_validate(
        state_json
    )

    versions = []

    for item in history_json:
        try:
            versions.append(
                StoryVersion.model_validate(item)
            )
        except Exception:
            continue

    return story, versions


def list_stories(
    user_id: str,
    access_token: str,
):
    """
    Return only this user's stories.
    """

    supabase = get_supabase(access_token)

    response = (
        supabase
        .table("stories")
        .select("*")
        .eq("user_id", user_id)
        .order(
            "updated_at",
            desc=True,
        )
        .execute()
    )

    return response.data or []