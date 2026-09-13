import uuid

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.ai.gemini import analyze_frame
from app.ai.groq import (
    adapt_current_story,
    generate_story_options,
)
from app.auth import get_current_user
from app.config import get_settings
from app.game.engine import (
    apply_action,
    build_game_state,
    build_object_mission,
    mission_render_entities,
    update_mission_from_detected_objects,
)
from app.schemas import (
    AdaptationRequest,
    FrameRequest,
    GameActionRequest,
    GameState,
    SceneModel,
    StartStoryRequest,
    StoryHistoryResponse,
    StoryOption,
    StoryState,
    StoryVersion,
)
from app.story_store import (
    create_story,
    get_story,
    list_stories,
    now_iso,
    parse_record,
    save_story,
)


settings = get_settings()


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="REALITY: UNSEEN",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# USER-SPECIFIC ACTIVE GAME STATE
# ============================================================
#
# Unlike the old version, these dictionaries are keyed by
# Supabase user ID.
#
# User A cannot overwrite User B's active game.
#
# Supabase remains the persistent database.
# These dictionaries are only the temporary live game state
# for this hackathon MVP.
# ============================================================

ACTIVE_GAMES: dict[str, GameState] = {}

ACTIVE_SCENES: dict[str, SceneModel] = {}

ACTIVE_VERSIONS: dict[
    str,
    list[StoryVersion],
] = {}


# ============================================================
# HEALTH
# ============================================================

@app.get("/api/health")
def health():
    return {
        "ok": True,
        "game": "REALITY: UNSEEN",
    }


# ============================================================
# WORLD ANALYSIS
# ============================================================

@app.post(
    "/api/world/analyze-frame",
    response_model=SceneModel,
)
def analyze_world(
    request: FrameRequest,
    current_user=Depends(get_current_user),
):
    user_id = str(current_user.id)

    try:
        scene = analyze_frame(
            request.image_base64,
            request.mime_type,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Gemini vision failed: "
                f"{exc}"
            ),
        )

    ACTIVE_SCENES[user_id] = scene

    return scene


# ============================================================
# STORY OPTIONS
# ============================================================

@app.post(
    "/api/story/options",
    response_model=list[StoryOption],
)
def story_options(
    scene: SceneModel,
    current_user=Depends(get_current_user),
):
    try:
        return generate_story_options(
            scene
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Story generation failed: "
                f"{exc}"
            ),
        )


# ============================================================
# START STORY
# ============================================================

@app.post(
    "/api/story/start",
    response_model=GameState,
)
def start_story(
    request: StartStoryRequest,
    current_user=Depends(get_current_user),
):
    user_id = str(current_user.id)

    # --------------------------------------------------------
    # Create canonical story
    # --------------------------------------------------------

    story = StoryState(
        story_id=str(uuid.uuid4()),

        title=request.story.title,

        genre=request.story.genre,

        gameplay_type=request.story.gameplay_type,

        premise=request.story.premise,

        objective=request.story.objective,

        chapter=1,

        status="active",

        scene_summary=request.scene.summary,

        current_event="The story begins.",

        difficulty=0.5,
    )

    # --------------------------------------------------------
    # Store current scene for this user
    # --------------------------------------------------------

    ACTIVE_SCENES[user_id] = request.scene

    # --------------------------------------------------------
    # Initial story history
    # --------------------------------------------------------

    ACTIVE_VERSIONS[user_id] = [

        StoryVersion(
            version=1,

            chapter=1,

            event="The story begins.",

            reason="Player selected this story.",

            timestamp=now_iso(),
        )
    ]

    # --------------------------------------------------------
    # Save story to Supabase
    # --------------------------------------------------------

    try:

        create_story(
            story,
            user_id,
            current_user.token,
        )

        save_story(
            story,
            ACTIVE_VERSIONS[user_id],
            user_id,
            current_user.token,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to save story: "
                f"{exc}"
            ),
        )

    # --------------------------------------------------------
    # Build game
    # --------------------------------------------------------

    game = build_game_state(
        story,
        request.scene.model_dump(),
    )

    ACTIVE_GAMES[user_id] = game

    return game


# ============================================================
# CURRENT GAME
# ============================================================

@app.get(
    "/api/game/state",
    response_model=GameState,
)
def get_game_state(
    current_user=Depends(get_current_user),
):
    user_id = str(current_user.id)

    game = ACTIVE_GAMES.get(user_id)

    if game is None:
        raise HTTPException(
            status_code=404,
            detail="No active game.",
        )

    return game


# ============================================================
# GAME ACTION
# ============================================================

@app.post(
    "/api/game/action",
    response_model=GameState,
)
def game_action(
    request: GameActionRequest,
    current_user=Depends(get_current_user),
):
    user_id = str(current_user.id)

    game = ACTIVE_GAMES.get(user_id)

    if game is None:
        raise HTTPException(
            status_code=404,
            detail="No active game.",
        )

    ACTIVE_GAMES[user_id] = apply_action(
        game,
        request.action,
    )

    game = ACTIVE_GAMES[user_id]

    mission_completed = bool(
        game.object_mission
        and game.object_mission.completed
    )

    should_adapt = (
        game.turn % 2 == 0
        or game.battle_over
        or mission_completed
    )

    scene = ACTIVE_SCENES.get(user_id)

    if should_adapt and scene is not None:

        try:

            adaptation = adapt_current_story(
                scene,
                game,
                request.action,
            )

        except Exception as exc:

            raise HTTPException(
                status_code=502,
                detail=(
                    "Story adaptation failed: "
                    f"{exc}"
                ),
            )

        # ----------------------------------------------------
        # Continue SAME canonical story
        # ----------------------------------------------------

        game.story.current_event = (
            adaptation.get(
                "event",
                game.story.current_event,
            )
        )

        game.story.objective = (
            adaptation.get(
                "new_objective",
                game.story.objective,
            )
        )

        game.story.difficulty = max(
            0.0,
            min(
                1.0,
                float(
                    adaptation.get(
                        "difficulty",
                        game.story.difficulty,
                    )
                ),
            ),
        )

        event = adaptation.get(
            "event",
            "The story continues.",
        )

        reason = adaptation.get(
            "reason",
            "The world changed.",
        )

        game.log.append(event)

        # ----------------------------------------------------
        # Save story version
        # ----------------------------------------------------

        versions = ACTIVE_VERSIONS.setdefault(
            user_id,
            [],
        )

        versions.append(
            StoryVersion(
                version=len(versions) + 1,

                chapter=game.story.chapter,

                event=event,

                reason=reason,

                timestamp=now_iso(),
            )
        )

        try:

            save_story(
                game.story,
                versions,
                user_id,
                current_user.token,
            )

        except Exception as exc:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Failed to save story "
                    f"history: {exc}"
                ),
            )

    ACTIVE_GAMES[user_id] = game

    return game


# ============================================================
# MISSION OBJECT SCAN
# ============================================================

@app.post(
    "/api/game/scan",
    response_model=GameState,
)
def scan_game_objects(
    scene: SceneModel,
    current_user=Depends(get_current_user),
):
    """
    Apply a fresh Gemini scene scan to the active non-battle
    mission and persist the resulting game/story state.

    Battle games can still use /api/game/action with action=scan.
    """

    user_id = str(current_user.id)

    game = ACTIVE_GAMES.get(user_id)

    if game is None:
        raise HTTPException(
            status_code=404,
            detail="No active game.",
        )

    ACTIVE_SCENES[user_id] = scene

    if game.gameplay_type == "battle":
        game = apply_action(game, "scan")
    else:
        # Older/stale active game states may have been created before
        # object missions were added. Initialize the mission lazily so
        # the frontend never gets stuck on an empty mission screen.
        if game.object_mission is None:
            detected_objects = [
                obj.model_dump()
                for obj in scene.objects
            ]
            mission = build_object_mission(
                game.story,
                detected_objects,
            )
            game.object_mission = mission
            game.render_entities = mission_render_entities(
                mission
            )

        game = update_mission_from_detected_objects(
            game,
            [obj.model_dump() for obj in scene.objects],
        )

    ACTIVE_GAMES[user_id] = game

    # Save completed/updated story state so mission progress
    # survives a resume within the persisted story record.
    versions = ACTIVE_VERSIONS.setdefault(
        user_id,
        [],
    )

    if (
        game.object_mission
        and game.object_mission.completed
    ):
        event = (
            f"{game.object_mission.title} completed."
        )

        versions.append(
            StoryVersion(
                version=len(versions) + 1,
                chapter=game.story.chapter,
                event=event,
                reason="Player found all required real-world objects.",
                timestamp=now_iso(),
            )
        )

    try:
        save_story(
            game.story,
            versions,
            user_id,
            current_user.token,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to save mission progress: "
                f"{exc}"
            ),
        )

    return game


# ============================================================
# MANUAL STORY ADAPTATION
# ============================================================

@app.post(
    "/api/story/adapt",
    response_model=GameState,
)
def manual_adaptation(
    request: AdaptationRequest,
    current_user=Depends(get_current_user),
):
    user_id = str(current_user.id)

    game = ACTIVE_GAMES.get(user_id)

    if game is None:
        raise HTTPException(
            status_code=404,
            detail="No active game.",
        )

    try:

        adaptation = adapt_current_story(
            request.scene,
            game,
            request.player_action,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                "Story adaptation failed: "
                f"{exc}"
            ),
        )

    # --------------------------------------------------------
    # Update SAME story
    # --------------------------------------------------------

    game.story.current_event = (
        adaptation.get(
            "event",
            game.story.current_event,
        )
    )

    game.story.objective = (
        adaptation.get(
            "new_objective",
            game.story.objective,
        )
    )

    game.story.difficulty = max(
        0.0,
        min(
            1.0,
            float(
                adaptation.get(
                    "difficulty",
                    game.story.difficulty,
                )
            ),
        ),
    )

    event = adaptation.get(
        "event",
        "The story continues.",
    )

    reason = adaptation.get(
        "reason",
        "The world changed.",
    )

    game.log.append(event)

    versions = ACTIVE_VERSIONS.setdefault(
        user_id,
        [],
    )

    versions.append(
        StoryVersion(
            version=len(versions) + 1,

            chapter=game.story.chapter,

            event=event,

            reason=reason,

            timestamp=now_iso(),
        )
    )

    try:

        save_story(
            game.story,
            versions,
            user_id,
            current_user.token,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to save story: "
                f"{exc}"
            ),
        )

    ACTIVE_GAMES[user_id] = game

    return game


# ============================================================
# STORY HISTORY
# ============================================================

@app.get(
    "/api/story/history"
)
def story_history(
    current_user=Depends(get_current_user),
):
    user_id = str(current_user.id)

    try:

        records = list_stories(
            user_id,
            current_user.token,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to load story history: "
                f"{exc}"
            ),
        )

    results = []

    for record in records:

        story, versions = parse_record(
            record
        )

        results.append({
            "story": story.model_dump(),

            "versions": [
                version.model_dump()
                for version in versions
            ],
        })

    return results


# ============================================================
# STORY HISTORY DETAIL
# ============================================================

@app.get(
    "/api/story/history/{story_id}",
    response_model=StoryHistoryResponse,
)
def story_history_detail(
    story_id: str,
    current_user=Depends(get_current_user),
):
    user_id = str(current_user.id)

    record = get_story(
        story_id,
        user_id,
        current_user.token,
    )

    if not record:

        raise HTTPException(
            status_code=404,
            detail="Story not found.",
        )

    story, versions = parse_record(
        record
    )

    return StoryHistoryResponse(
        story=story,
        versions=versions,
    )


# ============================================================
# RESUME STORY
# ============================================================

@app.post(
    "/api/story/resume/{story_id}",
    response_model=GameState,
)
def resume_story(
    story_id: str,
    current_user=Depends(get_current_user),
):
    user_id = str(current_user.id)

    record = get_story(
        story_id,
        user_id,
        current_user.token,
    )

    if not record:

        raise HTTPException(
            status_code=404,
            detail="Story not found.",
        )

    story, versions = parse_record(
        record
    )

    ACTIVE_VERSIONS[user_id] = versions

    # --------------------------------------------------------
    # Use the user's current scene if available.
    # Otherwise create a safe fallback scene.
    # --------------------------------------------------------

    scene = ACTIVE_SCENES.get(
        user_id
    )

    if scene is not None:

        scene_data = scene.model_dump()

    else:

        scene_data = {
            "environment": "unknown",

            "summary":
                story.scene_summary,

            "crowd_density": "none",

            "objects": [],

            "player_visible": False,

            "player_bbox": {
                "x": 0,
                "y": 0,
                "width": 0,
                "height": 0,
            },
        }

    game = build_game_state(
        story,
        scene_data,
    )

    ACTIVE_GAMES[user_id] = game

    return game


# ============================================================
# RESET
# ============================================================

@app.post(
    "/api/world/reset"
)
def reset_world(
    current_user=Depends(get_current_user),
):
    user_id = str(current_user.id)

    ACTIVE_GAMES.pop(
        user_id,
        None,
    )

    ACTIVE_SCENES.pop(
        user_id,
        None,
    )

    ACTIVE_VERSIONS.pop(
        user_id,
        None,
    )

    return {
        "status": "reset"
    }