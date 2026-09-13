from typing import Literal, Optional

from pydantic import BaseModel, Field


# ============================================================
# GAMEPLAY TYPES
# ============================================================

GameplayType = Literal[
    "battle",
    "hunt",
    "collection",
    "puzzle",
    "exploration",
    "survival",
    "stealth",
    "rescue",
]


# ============================================================
# WORLD / VISION
# ============================================================

class BoundingBox(BaseModel):
    """
    Normalized bounding box.

    x      = horizontal position
    y      = vertical position
    width  = box width
    height = box height
    """

    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0


class DetectedObject(BaseModel):
    """
    Object detected inside the real-world camera frame.
    """

    id: str

    label: str

    category: str = "object"

    confidence: float = Field(
        default=0.5,
        ge=0,
        le=1,
    )

    # Normalized:
    # [x, y, width, height]
    bbox: list[float] = Field(
        min_length=4,
        max_length=4,
    )

    # How important this object is to the current story.
    story_relevance: float = Field(
        default=0,
        ge=0,
        le=100,
    )


class SceneModel(BaseModel):
    """
    Complete understanding of the camera frame.
    """

    environment: str

    summary: str

    crowd_density: Literal[
        "none",
        "low",
        "medium",
        "high",
    ] = "none"

    objects: list[DetectedObject] = Field(
        default_factory=list
    )

    player_visible: bool = False

    # Never nullable because Gemini schema conversion
    # can have problems with nullable nested fields.
    #
    # If player is not detected, values remain 0.
    player_bbox: BoundingBox = Field(
        default_factory=BoundingBox
    )


# ============================================================
# STORY GENERATION
# ============================================================

class StoryOption(BaseModel):
    """
    One possible game/story generated from the
    scanned real-world environment.
    """

    id: str

    title: str

    genre: str

    # IMPORTANT:
    # The AI decides what type of game this reality
    # should become.
    gameplay_type: GameplayType = "exploration"

    premise: str

    objective: str

    tone: str


class StoryState(BaseModel):
    """
    Canonical story/game state.

    story_id MUST remain the same throughout
    the entire gameplay experience.

    The AI may adapt:
        - events
        - difficulty
        - enemies
        - clues
        - routes
        - objectives

    But it should preserve the original story identity.
    """

    story_id: str

    title: str

    genre: str

    gameplay_type: GameplayType = "exploration"

    premise: str

    objective: str

    chapter: int = 1

    status: Literal[
        "active",
        "completed",
        "paused",
    ] = "active"

    scene_summary: str = ""

    current_event: str = ""

    difficulty: float = Field(
        default=0.5,
        ge=0,
        le=1,
    )


# ============================================================
# STORY HISTORY
# ============================================================

class StoryVersion(BaseModel):
    """
    One entry in the story history.
    """

    version: int

    chapter: int

    event: str

    reason: str

    timestamp: str


class StoryHistoryResponse(BaseModel):
    story: StoryState

    versions: list[StoryVersion]


# ============================================================
# STORY REQUESTS
# ============================================================

class StartStoryRequest(BaseModel):
    story: StoryOption

    scene: SceneModel


# ============================================================
# GAMEPLAY ACTIONS
# ============================================================

class GameActionRequest(BaseModel):
    """
    Player action.

    Battle:
        attack
        defend
        special
        scan

    Non-battle:
        scan is the primary action.
    """

    action: Literal[
        "attack",
        "defend",
        "special",
        "scan",
    ]

    target_id: Optional[str] = None


# ============================================================
# OBJECTIVE / MISSION
# ============================================================

class MissionTarget(BaseModel):
    """
    Object that the player needs to find/interact with
    in the real-world camera.
    """

    id: str

    label: str

    description: str = ""

    required: bool = True

    found: bool = False

    confidence: float = Field(
        default=0.0,
        ge=0,
        le=1,
    )

    bbox: list[float] = Field(
        default_factory=lambda: [0.0, 0.0, 0.0, 0.0],
        min_length=4,
        max_length=4,
    )


class ObjectMission(BaseModel):
    """
    Mission used by non-battle gameplay.

    Example:

        Find:
        - bottle
        - pen
        - paper

    The player scans the camera and the AI checks
    whether the required objects are visible.
    """

    mission_type: GameplayType = "hunt"

    title: str

    description: str

    targets: list[MissionTarget] = Field(
        default_factory=list
    )

    completed: bool = False

    progress: int = 0

    total: int = 0


# ============================================================
# GAME STATE
# ============================================================

class GameState(BaseModel):
    """
    Complete runtime state of the game.

    The same GameState supports both:

        BATTLE
        HUNT
        COLLECTION
        PUZZLE
        EXPLORATION
        SURVIVAL
        STEALTH
        RESCUE
    """

    story: StoryState

    # --------------------------------------------------------
    # GAMEPLAY TYPE
    # --------------------------------------------------------

    gameplay_type: GameplayType = "exploration"

    # --------------------------------------------------------
    # BATTLE STATE
    # --------------------------------------------------------

    player_hp: int = 100

    enemy_hp: int = 0

    enemy: Optional[dict] = None

    # --------------------------------------------------------
    # NON-BATTLE MISSION
    # --------------------------------------------------------

    object_mission: Optional[ObjectMission] = None

    # --------------------------------------------------------
    # COMMON GAME STATE
    # --------------------------------------------------------

    turn: int = 1

    log: list[str] = Field(
        default_factory=list
    )

    render_entities: list[dict] = Field(
        default_factory=list
    )

    battle_over: bool = False


# ============================================================
# AI STORY ADAPTATION
# ============================================================

class AdaptationRequest(BaseModel):
    """
    Request sent to the AI Game Director when the
    environment or player behavior changes.
    """

    scene: SceneModel

    player_action: str

    game_state: GameState


# ============================================================
# CAMERA FRAME
# ============================================================

class FrameRequest(BaseModel):
    """
    Camera image sent to the vision pipeline.
    """

    image_base64: str

    mime_type: str = "image/jpeg"