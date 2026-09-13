from copy import deepcopy
import random

from app.ai.groq import choose_enemy
from app.schemas import (
    GameState,
    StoryState,
    ObjectMission,
    MissionTarget,
)


# ============================================================
# FALLBACK CREATURES
# ============================================================

FALLBACK_CREATURES = {
    "laptop": {
        "name": "Cybermite",
        "type": "Electric",
        "abilities": ["Byte Bite", "Data Burst", "Glitch Shock"],
        "animation": "electric",
        "special": "Data Burst",
    },
    "chair": {
        "name": "Ironback",
        "type": "Metal",
        "abilities": ["Steel Slam", "Back Bash", "Iron Charge"],
        "animation": "heavy",
        "special": "Steel Slam",
    },
    "plant": {
        "name": "Thornling",
        "type": "Nature",
        "abilities": ["Vine Strike", "Leaf Storm", "Thorn Trap"],
        "animation": "nature",
        "special": "Vine Trap",
    },
    "fan": {
        "name": "Wind Talon",
        "type": "Air",
        "abilities": ["Wind Slash", "Gust Attack", "Cyclone"],
        "animation": "wind",
        "special": "Cyclone",
    },
    "monitor": {
        "name": "Screen Wraith",
        "type": "Dark",
        "abilities": ["Pixel Blast", "Glitch Wave", "Screen Drain"],
        "animation": "glitch",
        "special": "Glitch Wave",
    },
    "phone": {
        "name": "Signal Phantom",
        "type": "Electric",
        "abilities": ["Signal Shock", "Static Pulse", "Frequency Break"],
        "animation": "electric",
        "special": "Signal Shock",
    },
    "door": {
        "name": "Gatekeeper",
        "type": "Mystic",
        "abilities": ["Reality Lock", "Portal Slam", "Dimension Break"],
        "animation": "mystic",
        "special": "Reality Lock",
    },
    "bottle": {
        "name": "Toxiblob",
        "type": "Toxic",
        "abilities": ["Toxic Splash", "Acid Bounce", "Poison Burst"],
        "animation": "toxic",
        "special": "Toxic Splash",
    },
}


# ============================================================
# HELPERS
# ============================================================

def normalize_label(label: str) -> str:
    return (
        str(label or "")
        .lower()
        .strip()
        .replace("_", " ")
        .replace("-", " ")
    )


def canonical_object_label(label: str) -> str:
    """
    Convert common Gemini labels into stable object names.
    """

    key = normalize_label(label)

    aliases = {
        "smartphone": "phone",
        "mobile": "phone",
        "mobile phone": "phone",
        "cell phone": "phone",
        "cellphone": "phone",
        "computer": "laptop",
        "notebook computer": "laptop",
        "display": "monitor",
        "screen": "monitor",
        "computer screen": "monitor",
        "spectacles": "spectacles",
        "eyeglasses": "spectacles",
        "eyeglass": "spectacles",
        "specs": "spectacles",
    }

    return aliases.get(key, key)


def get_fallback_creature(
    label: str,
    genre: str = "adventure",
) -> dict:
    """
    Object-specific local fallback.

    Never use a generic 'Reality Echo' creature.
    """

    key = canonical_object_label(label)

    if key in FALLBACK_CREATURES:
        creature = dict(FALLBACK_CREATURES[key])
    else:
        creature = {
            "name": f"{str(label).title()} Beast",
            "type": "Reality",
            "abilities": [
                "Object Strike",
                "Reality Surge",
                "World Shift",
            ],
            "animation": "mystic",
            "special": "Reality Break",
        }

    creature["mission"] = (
        f"Defeat the {creature['name']} born from "
        f"the {label} and complete your {genre} objective."
    )

    return creature


def get_enemy_for_object(
    label: str,
    genre: str = "adventure",
) -> dict:
    """
    Generate an original creature from the real-world object.

    AI is attempted first. If generation fails, use the
    local object-specific fallback.
    """

    fallback = get_fallback_creature(label, genre)

    try:
        enemy_base = choose_enemy(label, genre)

        if (
            not enemy_base
            or str(enemy_base.get("name", "")).strip().lower()
            == "reality echo"
        ):
            return fallback

        return {
            "name": enemy_base.get("name", fallback["name"]),
            "type": enemy_base.get("type", fallback["type"]),
            "abilities": enemy_base.get(
                "abilities",
                fallback["abilities"],
            ),
            "animation": enemy_base.get(
                "animation",
                fallback["animation"],
            ),
            "special": enemy_base.get(
                "special",
                fallback["special"],
            ),
            "mission": enemy_base.get(
                "mission",
                fallback["mission"],
            ),
        }

    except TypeError:
        # Backward compatibility with choose_enemy(label)
        try:
            enemy_base = choose_enemy(label)

            if (
                not enemy_base
                or str(enemy_base.get("name", "")).strip().lower()
                == "reality echo"
            ):
                return fallback

            return {
                "name": enemy_base.get("name", fallback["name"]),
                "type": enemy_base.get("type", fallback["type"]),
                "abilities": enemy_base.get(
                    "abilities",
                    fallback["abilities"],
                ),
                "animation": enemy_base.get(
                    "animation",
                    fallback["animation"],
                ),
                "special": enemy_base.get(
                    "special",
                    fallback["special"],
                ),
                "mission": enemy_base.get(
                    "mission",
                    fallback["mission"],
                ),
            }

        except Exception:
            return fallback

    except Exception:
        return fallback


# ============================================================
# ENEMY GENERATION
# ============================================================

def build_enemy(
    candidate: dict,
    difficulty: float = 0.5,
    genre: str = "adventure",
) -> dict:

    label = candidate.get("label", "environment")

    enemy_base = get_enemy_for_object(label, genre)

    relevance = float(
        candidate.get("story_relevance", 50)
    )

    difficulty_bonus = int(difficulty * 25)

    max_hp = (
        80
        + int(relevance * 0.4)
        + difficulty_bonus
    )

    attack = (
        10
        + int(relevance * 0.08)
        + int(difficulty * 8)
    )

    defense = (
        6
        + int(relevance * 0.05)
        + int(difficulty * 6)
    )

    return {
        "id": f"enemy_{candidate.get('id', '01')}",
        "source_object": label,
        "source_object_id": candidate.get("id"),
        "name": enemy_base["name"],
        "type": enemy_base["type"],
        "hp": max_hp,
        "max_hp": max_hp,
        "attack": attack,
        "defense": defense,
        "abilities": enemy_base["abilities"],
        "special": enemy_base["special"],
        "mission": enemy_base.get(
            "mission",
            f"Defeat the creature born from {label}.",
        ),
        "genre": genre,
        "animation": enemy_base["animation"],
        "bbox": candidate.get(
            "bbox",
            [0.5, 0.3, 0.2, 0.3],
        ),
        "animation_state": "transform",
        "is_ai_generated": True,
        "manifestation": (
            f"{label} has transformed into "
            f"{enemy_base['name']} for the {genre} story."
        ),
    }


# ============================================================
# NON-BATTLE OBJECT MISSIONS
# ============================================================

def build_object_mission(
    story: StoryState,
    objects: list[dict],
) -> ObjectMission:
    """
    Build a camera-based mission for non-battle games.

    Example:

        Find the:
        - bottle
        - pen
        - paper

    The player then scans the camera to find them.
    """

    relevant_objects = sorted(
        objects,
        key=lambda obj: float(
            obj.get("story_relevance", 0)
        ),
        reverse=True,
    )

    # Keep missions small enough to be playable.
    candidates = [
        obj
        for obj in relevant_objects
        if obj.get("label")
    ][:4]

    targets = []

    for index, obj in enumerate(candidates):
        label = str(obj.get("label", "object"))

        target_id = (
            f"mission_target_{obj.get('id', index)}"
        )

        description = (
            f"Find the {label} visible in the "
            f"real-world environment."
        )

        targets.append(
            MissionTarget(
                id=target_id,
                label=label,
                description=description,
                required=True,
                found=False,
                confidence=float(
                    obj.get("confidence", 0)
                ),
                bbox=obj.get(
                    "bbox",
                    [0.0, 0.0, 0.0, 0.0],
                ),
            )
        )

    mission_titles = {
        "hunt": "Reality Hunt",
        "collection": "Reality Collection",
        "puzzle": "Reality Puzzle",
        "exploration": "Reality Exploration",
        "survival": "Reality Survival",
        "stealth": "Reality Stealth",
        "rescue": "Reality Rescue",
    }

    gameplay_type = getattr(
        story,
        "gameplay_type",
        "exploration",
    )

    title = mission_titles.get(
        gameplay_type,
        "Reality Mission",
    )

    if gameplay_type == "hunt":
        description = (
            "Search the real world through your camera "
            "and find every required object."
        )
    elif gameplay_type == "collection":
        description = (
            "Collect the required objects from your "
            "real-world environment."
        )
    elif gameplay_type == "puzzle":
        description = (
            "Find the objects that contain the clues "
            "needed to solve the puzzle."
        )
    elif gameplay_type == "rescue":
        description = (
            "Locate the required objects to complete "
            "the rescue sequence."
        )
    else:
        description = (
            f"Complete the objective: {story.objective}"
        )

    return ObjectMission(
        mission_type=gameplay_type,
        title=title,
        description=description,
        targets=targets,
        completed=False,
        progress=0,
        total=len(targets),
    )


def mission_render_entities(
    mission: ObjectMission,
) -> list[dict]:
    """
    Convert mission targets into frontend render entities.
    """

    entities = []

    for target in mission.targets:
        entities.append(
            {
                "id": target.id,
                "type": "mission_object",
                "label": target.label,
                "bbox": target.bbox,
                "found": target.found,
                "importance": 100 if target.required else 50,
            }
        )

    return entities


def update_mission_from_detected_objects(
    game: GameState,
    detected_objects: list[dict],
) -> GameState:
    """
    Compare a fresh Gemini scan against mission targets.

    This function is useful when main.py receives the
    newly scanned SceneModel.

    Matching is intentionally label-based for the MVP.
    """

    updated = deepcopy(game)

    mission = updated.object_mission

    if not mission:
        return updated

    detected_labels = {
        canonical_object_label(
            obj.get("label", "")
        )
        for obj in detected_objects
        if obj.get("label")
    }

    for target in mission.targets:
        target_key = canonical_object_label(
            target.label
        )

        if target_key in detected_labels:
            if not target.found:
                target.found = True
                updated.log.append(
                    f"FOUND: {target.label}"
                )

    mission.progress = sum(
        1
        for target in mission.targets
        if target.found
    )

    mission.total = len(mission.targets)

    if (
        mission.total > 0
        and mission.progress >= mission.total
    ):
        mission.completed = True
        updated.story.status = "completed"

        updated.log.append(
            "Mission complete. Reality stabilized."
        )

    updated.render_entities = mission_render_entities(
        mission
    )

    updated.turn += 1

    return updated


# ============================================================
# INITIAL GAME CREATION
# ============================================================

def build_game_state(
    story: StoryState,
    scene: dict,
) -> GameState:

    objects = scene.get("objects", [])

    gameplay_type = getattr(
        story,
        "gameplay_type",
        "exploration",
    )

    # --------------------------------------------------------
    # NO OBJECTS
    # --------------------------------------------------------

    if not objects:

        if gameplay_type == "battle":
            return GameState(
                story=story,
                gameplay_type=gameplay_type,
                player_hp=100,
                enemy_hp=0,
                enemy=None,
                turn=1,
                log=[
                    "No suitable world object was detected.",
                    f"Mission started: {story.objective}",
                ],
                render_entities=[],
                battle_over=True,
            )

        mission = build_object_mission(
            story,
            [],
        )

        return GameState(
            story=story,
            gameplay_type=gameplay_type,
            player_hp=100,
            enemy_hp=0,
            enemy=None,
            object_mission=mission,
            turn=1,
            log=[
                "No objects were detected.",
                "Scan the environment again to continue.",
            ],
            render_entities=[],
            battle_over=True,
        )

    # --------------------------------------------------------
    # BATTLE GAME
    # --------------------------------------------------------

    if gameplay_type == "battle":

        relevant_objects = sorted(
            objects,
            key=lambda obj: float(
                obj.get("story_relevance", 0)
            ),
            reverse=True,
        )

        candidate = relevant_objects[0]

        difficulty = float(
            getattr(
                story,
                "difficulty",
                0.5,
            )
        )

        genre = (
            getattr(
                story,
                "genre",
                "adventure",
            )
            or "adventure"
        )

        enemy = build_enemy(
            candidate,
            difficulty,
            genre,
        )

        render_entities = [
            {
                "id": enemy["id"],
                "type": "enemy",
                "label": enemy["name"],
                "source_object": enemy["source_object"],
                "bbox": enemy["bbox"],
                "animation": enemy["animation"],
                "animation_state": "transform",
                "importance": 100,
            }
        ]

        for obj in relevant_objects[:6]:

            if (
                candidate
                and obj.get("id")
                == candidate.get("id")
            ):
                continue

            relevance = float(
                obj.get("story_relevance", 0)
            )

            if relevance < 40:
                continue

            render_entities.append(
                {
                    "id": obj.get("id"),
                    "type": "story_object",
                    "label": obj.get("label"),
                    "bbox": obj.get(
                        "bbox",
                        [0.5, 0.3, 0.2, 0.3],
                    ),
                    "importance": relevance,
                }
            )

        log = [
            f"Mission started: {story.objective}",
            f"Reality detected {len(objects)} objects.",
            (
                f"{enemy['source_object']} "
                f"began transforming..."
            ),
            (
                f"{enemy['name']} appeared from "
                f"the {enemy['source_object']}."
            ),
            (
                f"AI mission: "
                f"{enemy.get('mission', story.objective)}"
            ),
        ]

        return GameState(
            story=story,
            gameplay_type="battle",
            player_hp=100,
            enemy_hp=enemy["hp"],
            enemy=enemy,
            object_mission=None,
            turn=1,
            log=log,
            render_entities=render_entities,
            battle_over=False,
        )

    # --------------------------------------------------------
    # NON-BATTLE GAME
    # --------------------------------------------------------

    mission = build_object_mission(
        story,
        objects,
    )

    render_entities = mission_render_entities(
        mission
    )

    log = [
        f"Mission started: {story.objective}",
        f"Reality detected {len(objects)} objects.",
        f"Game mode: {gameplay_type.upper()}",
        mission.description,
    ]

    if mission.targets:
        log.append(
            "Required objects: "
            + ", ".join(
                target.label
                for target in mission.targets
            )
        )
    else:
        log.append(
            "No mission targets were selected. "
            "Scan the environment again."
        )

    return GameState(
        story=story,
        gameplay_type=gameplay_type,
        player_hp=100,
        enemy_hp=0,
        enemy=None,
        object_mission=mission,
        turn=1,
        log=log,
        render_entities=render_entities,
        battle_over=mission.completed,
    )


# ============================================================
# BATTLE ACTIONS
# ============================================================

def apply_battle_action(
    state: GameState,
    action: str,
) -> GameState:

    game = deepcopy(state)

    if game.battle_over:
        game.log.append(
            "The battle is already over."
        )
        return game

    enemy = game.enemy

    if not enemy:
        game.battle_over = True
        return game

    # --------------------------------------------------------
    # ATTACK
    # --------------------------------------------------------

    if action == "attack":

        base_damage = 18

        damage = max(
            8,
            base_damage
            - int(
                enemy.get("defense", 0)
                * 0.25
            ),
        )

        game.enemy_hp = max(
            0,
            game.enemy_hp - damage,
        )

        enemy["animation_state"] = "hit"

        game.log.append(
            f"You used Reality Strike "
            f"for {damage} damage."
        )

    # --------------------------------------------------------
    # SPECIAL
    # --------------------------------------------------------

    elif action == "special":

        damage = 28

        game.enemy_hp = max(
            0,
            game.enemy_hp - damage,
        )

        game.player_hp = max(
            0,
            game.player_hp - 4,
        )

        enemy["animation_state"] = "special"

        game.log.append(
            f"You used Reality Shift "
            f"for {damage} damage."
        )

    # --------------------------------------------------------
    # DEFEND
    # --------------------------------------------------------

    elif action == "defend":

        enemy["animation_state"] = "attack"

        game.log.append(
            "You raised a reality shield."
        )

    # --------------------------------------------------------
    # SCAN
    # --------------------------------------------------------

    elif action == "scan":

        enemy["animation_state"] = "scan"

        game.log.append(
            f"SCAN COMPLETE: {enemy['name']} "
            f"originates from "
            f"{enemy['source_object']}."
        )

    else:

        game.log.append(
            f"Unknown battle action: {action}"
        )

        return game

    # --------------------------------------------------------
    # ENEMY DEFEATED
    # --------------------------------------------------------

    if game.enemy_hp <= 0:

        game.enemy_hp = 0

        enemy["animation_state"] = "defeat"

        game.battle_over = True

        game.story.status = "completed"

        game.log.append(
            f"{enemy['name']} was defeated."
        )

        game.log.append(
            "Reality stabilizing..."
        )

        return game

    # --------------------------------------------------------
    # ENEMY RESPONSE
    # --------------------------------------------------------

    difficulty = float(
        getattr(
            game.story,
            "difficulty",
            0.5,
        )
    )

    enemy_damage = int(
        enemy.get("attack", 13)
    )

    enemy_damage += int(
        difficulty * 5
    )

    if action == "defend":
        enemy_damage = max(
            3,
            enemy_damage // 3,
        )

    elif action == "scan":
        enemy_damage = max(
            5,
            enemy_damage - 3,
        )

    abilities = enemy.get(
        "abilities",
        ["Reality Pulse"],
    )

    ability_index = (
        game.turn % len(abilities)
    )

    ability = abilities[ability_index]

    enemy["animation_state"] = "attack"

    game.player_hp = max(
        0,
        game.player_hp - enemy_damage,
    )

    game.log.append(
        f"{enemy['name']} used {ability} "
        f"for {enemy_damage} damage."
    )

    game.turn += 1

    if game.player_hp <= 0:

        game.player_hp = 0

        enemy["animation_state"] = "victory"

        game.battle_over = True

        game.story.status = "paused"

        game.log.append(
            "You were overwhelmed."
        )

    else:

        enemy["animation_state"] = "idle"

    return game


# ============================================================
# NON-BATTLE ACTIONS
# ============================================================

def apply_non_battle_action(
    state: GameState,
    action: str,
) -> GameState:
    """
    Handle actions for hunt, collection, puzzle,
    exploration, survival, stealth and rescue.

    A fresh camera detection can be applied separately
    with update_mission_from_detected_objects().
    """

    game = deepcopy(state)

    mission = game.object_mission

    if not mission:
        game.log.append(
            "No active object mission."
        )
        return game

    if mission.completed:
        game.log.append(
            "Mission already completed."
        )
        return game

    if action == "scan":

        game.log.append(
            "SCAN READY: point the camera at the "
            "real-world objects you need to find."
        )

        game.turn += 1

        return game

    if action in {
        "attack",
        "defend",
        "special",
    }:

        game.log.append(
            f"{action.upper()} is not used in "
            f"{game.gameplay_type.upper()} mode."
        )

        return game

    game.log.append(
        f"Unknown action: {action}"
    )

    return game


# ============================================================
# PUBLIC ACTION ROUTER
# ============================================================

def apply_action(
    state: GameState,
    action: str,
) -> GameState:
    """
    Route the player action according to the selected
    gameplay type.

    Battle:
        attack / defend / special / scan

    Everything else:
        scan-based object mission.
    """

    gameplay_type = getattr(
        state,
        "gameplay_type",
        getattr(
            state.story,
            "gameplay_type",
            "battle",
        ),
    )

    if gameplay_type == "battle":
        return apply_battle_action(
            state,
            action,
        )

    return apply_non_battle_action(
        state,
        action,
    )
