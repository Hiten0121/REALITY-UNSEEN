import json

from groq import Groq

from app.config import get_settings
from app.safety import safety_check
from app.schemas import GameState, SceneModel, StoryOption


settings = get_settings()


# ============================================================
# GROQ CLIENT
# ============================================================

def get_client():
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is missing")
    return Groq(api_key=settings.groq_api_key)


def json_completion(system_prompt: str, user_prompt: str) -> dict:
    """Run a Groq completion that must return valid JSON."""
    client = get_client()

    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {
                "role": "system",
                "content": (
                    system_prompt
                    + "\n\nReturn valid JSON only. "
                    "Do not use markdown fences."
                ),
            },
            {
                "role": "user",
                "content": (
                    user_prompt
                    + "\n\nRespond using JSON."
                ),
            },
        ],
        temperature=0.8,
        max_tokens=2200,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Groq returned an empty response.")

    return json.loads(content)


# ============================================================
# STORY GENERATION
# ============================================================

def generate_story_options(scene: SceneModel) -> list[StoryOption]:
    """
    Generate 3 or 4 substantially different games from the
    same real-world camera scene.

    Not every generated game should be a battle.
    """

    system_prompt = """
You are the Game Director for REALITY: UNSEEN.

The player has scanned a real-world environment.

Transform that SAME environment into 3 or 4 substantially
different fictional game concepts.

Allowed genres:
- mystery
- fantasy
- sci-fi
- adventure
- survival
- exploration
- supernatural
- puzzle

Allowed gameplay_type values:
- battle
- hunt
- collection
- puzzle
- exploration
- survival
- stealth
- rescue

IMPORTANT:
Do NOT make every story a battle.

Choose gameplay_type based on what makes the scanned
environment interesting.

Examples:
- Many ordinary objects -> hunt or collection
- Objects can be clues -> puzzle or mystery
- Interesting environment -> exploration
- Genuine fictional danger -> battle or survival
- Avoiding detection -> stealth
- Finding something that must be recovered -> rescue or hunt

NON-BATTLE RULE:
When gameplay_type is NOT "battle":
- Do not create enemies.
- Do not require combat.
- Use real-world objects as targets, clues, collectibles,
  locations, or mission elements.

BATTLE RULE:
Only use "battle" when combat genuinely fits the story.
Enemies must be fictional/environmental game entities.
Never make real people or protected groups enemies.
Never create sexual or hate content.

Every story must:
1. Be playable with a camera-based web application.
2. Use the scanned environment meaningfully.
3. Have a clear objective.
4. Be substantially different from the other stories.
5. Be safe and easy to understand.

Return EXACTLY this JSON:

{
  "stories": [
    {
      "id": "unique_id",
      "title": "short game title",
      "genre": "genre",
      "gameplay_type": "battle|hunt|collection|puzzle|exploration|survival|stealth|rescue",
      "premise": "short fictional premise",
      "objective": "clear player objective",
      "tone": "short tone description"
    }
  ]
}

Return 3 or 4 stories.
"""

    user_prompt = (
        "Here is the camera scene as JSON:\n"
        + scene.model_dump_json()
    )

    try:
        data = json_completion(system_prompt, user_prompt)
    except Exception as exc:
        print("GROQ STORY ERROR:", str(exc))
        return []

    stories: list[StoryOption] = []

    for item in data.get("stories", [])[:4]:
        allowed, violations = safety_check(item)

        if not allowed:
            print("STORY REJECTED BY SAFETY:", violations)
            continue

        try:
            stories.append(StoryOption.model_validate(item))
        except Exception as exc:
            print("INVALID STORY OPTION:", str(exc))

    return stories


# ============================================================
# STORY ADAPTATION
# ============================================================

def adapt_current_story(
    scene: SceneModel,
    game_state: GameState,
    player_action: str,
) -> dict:
    """
    Adapt the selected story without replacing it.

    story_id and gameplay_type remain stable.
    Non-battle games cannot suddenly become combat games.
    """

    gameplay_type = getattr(
        game_state,
        "gameplay_type",
        getattr(game_state.story, "gameplay_type", "exploration"),
    )

    system_prompt = """
You are the AI Game Director for REALITY: UNSEEN.

The player has ALREADY selected a story.

The story is CANONICAL.

CRITICAL RULES:
- Never replace the story with an unrelated story.
- Never change story_id.
- Never change gameplay_type.
- Preserve the original premise.

The current gameplay type is supplied in the payload.

For NON-BATTLE games:
- Do not introduce enemies or combat.
- Adapt using targets, clues, routes, puzzle steps,
  exploration discoveries, stealth consequences,
  rescue progress, collection goals, or helpful hints.

For BATTLE games:
- You may adapt fictional enemies, enemy difficulty,
  attacks, hazards, objectives, and consequences.

If the player struggles:
- provide a clue
- simplify the next objective
- reduce pressure
- provide an alternate route
- make the next step easier

If the player dominates:
- increase challenge
- add a complication
- create a more complex objective
- for battle only, a stronger fictional challenge may appear

Do not tell the player that an algorithm changed difficulty.

Return EXACTLY this JSON:

{
  "event": "new story event",
  "reason": "why this event happened",
  "new_objective": "updated objective",
  "difficulty": 0.0,
  "target_object_label": "object relevant to the next step or empty string",
  "target_reason": "why this object matters",
  "enemy_object_label": "ONLY for battle; otherwise empty string",
  "enemy_reason": "ONLY for battle; otherwise empty string"
}

Difficulty must be between 0.0 and 1.0.
"""

    payload = {
        "current_story": game_state.story.model_dump(),
        "game_state": game_state.model_dump(),
        "player_action": player_action,
        "new_scene": scene.model_dump(),
        "current_gameplay_type": gameplay_type,
    }

    try:
        data = json_completion(
            system_prompt,
            json.dumps(payload),
        )
    except Exception as exc:
        print("GROQ ADAPTATION ERROR:", str(exc))
        return {
            "event": "A new path through the environment reveals itself.",
            "reason": "Safe fallback adaptation.",
            "new_objective": game_state.story.objective,
            "difficulty": max(0.2, game_state.story.difficulty - 0.1),
            "target_object_label": "",
            "target_reason": "",
            "enemy_object_label": "",
            "enemy_reason": "",
        }

    allowed, violations = safety_check(data)

    if not allowed:
        return {
            "event": "A hidden route reveals a safer path forward.",
            "reason": "Safety fallback.",
            "new_objective": game_state.story.objective,
            "difficulty": max(0.2, game_state.story.difficulty - 0.1),
            "target_object_label": "",
            "target_reason": "",
            "enemy_object_label": "",
            "enemy_reason": "",
            "safety_violations": violations,
        }

    if gameplay_type != "battle":
        data["enemy_object_label"] = ""
        data["enemy_reason"] = ""

    return data


# ============================================================
# OBJECT -> CREATURE GENERATION
# ============================================================

def choose_enemy(
    object_label: str,
    genre: str = "adventure",
) -> dict:
    """
    Return an original creature derived from a real-world
    object and the selected genre.

    This is used ONLY by battle gameplay.
    """

    label = str(object_label or "").lower().strip()
    genre = str(genre or "adventure").lower().strip()

    if (
        "spectacle" in label
        or "eyeglass" in label
        or "glasses" in label
        or "specs" in label
    ):
        object_key = "spectacles"
    elif (
        "laptop" in label
        or "computer" in label
        or "notebook" in label
    ):
        object_key = "laptop"
    elif (
        "phone" in label
        or "mobile" in label
        or "smartphone" in label
    ):
        object_key = "phone"
    elif "chair" in label:
        object_key = "chair"
    elif (
        "plant" in label
        or "tree" in label
        or "flower" in label
    ):
        object_key = "plant"
    elif "fan" in label:
        object_key = "fan"
    elif (
        "display" in label
        or "monitor" in label
        or "screen" in label
    ):
        object_key = "display"
    else:
        object_key = "object"

    if "fantasy" in genre:
        genre_key = "fantasy"
    elif "action" in genre or "shoot" in genre:
        genre_key = "action"
    elif "sci" in genre:
        genre_key = "sci-fi"
    elif "mystery" in genre:
        genre_key = "mystery"
    else:
        genre_key = "adventure"

    creatures = {'spectacles': {'fantasy': {'name': 'Spectral Specs', 'type': 'Mystic', 'abilities': ['Lens Curse', 'Mirror Ray', 'Illusion Sight'], 'special': 'Vision Break', 'animation': 'magic', 'mission': 'Recover the enchanted lens before the Spectral Specs escape.'}, 'action': {'name': 'Scope Stalker', 'type': 'Tactical', 'abilities': ['Precision Shot', 'Target Lock', 'Scope Flash'], 'special': 'Deadeye Burst', 'animation': 'shooting', 'mission': 'Defeat the Scope Stalker before it marks your position.'}, 'sci-fi': {'name': 'OptiDrone', 'type': 'Cyber', 'abilities': ['Laser Focus', 'Optical Scan', 'Photon Burst'], 'special': 'Neural Lock', 'animation': 'energy', 'mission': 'Disable the OptiDrone before it completes its surveillance scan.'}, 'mystery': {'name': 'Vision Phantom', 'type': 'Illusion', 'abilities': ['False Image', 'Clue Distortion', 'Shadow Glimpse'], 'special': 'Memory Blur', 'animation': 'mystic', 'mission': 'Expose the Vision Phantom and recover the hidden clue.'}}, 'laptop': {'fantasy': {'name': 'Arcane Byte', 'type': 'Magic', 'abilities': ['Rune Crash', 'Mana Code', 'Spell Firewall'], 'special': 'Ancient Algorithm', 'animation': 'magic', 'mission': 'Decode the ancient spell hidden inside the Arcane Byte.'}, 'action': {'name': 'Cyber Raider', 'type': 'Combat', 'abilities': ['Data Strike', 'Rapid Fire', 'Firewall Slam'], 'special': 'Overclock Assault', 'animation': 'shooting', 'mission': 'Destroy the Cyber Raider before it breaches the network.'}, 'sci-fi': {'name': 'Cybermite', 'type': 'Electric', 'abilities': ['Byte Bite', 'Data Burst', 'Glitch Shock'], 'special': 'Overclock', 'animation': 'electric', 'mission': 'Stop the Cybermite from corrupting the digital network.'}, 'mystery': {'name': 'Glitch Phantom', 'type': 'Digital', 'abilities': ['File Vanish', 'Ghost Process', 'Memory Leak'], 'special': 'System Rewrite', 'animation': 'glitch', 'mission': 'Find the missing message hidden inside the Glitch Phantom.'}}, 'phone': {'fantasy': {'name': 'Signal Sprite', 'type': 'Mystic', 'abilities': ['Whisper Call', 'Rune Message', 'Echo Charm'], 'special': 'Royal Summons', 'animation': 'magic', 'mission': 'Answer the magical call and discover who summoned the Signal Sprite.'}, 'action': {'name': 'Signal Hunter', 'type': 'Tactical', 'abilities': ['Pulse Shot', 'Tracking Ping', 'Shock Strike'], 'special': 'Target Lock', 'animation': 'shooting', 'mission': 'Track and defeat the Signal Hunter.'}, 'sci-fi': {'name': 'Volt Drone', 'type': 'Electric', 'abilities': ['Electric Pulse', 'Signal Beam', 'EMP Burst'], 'special': 'System Overload', 'animation': 'electric', 'mission': 'Destroy the Volt Drone before it overloads the communication grid.'}, 'mystery': {'name': 'Message Wraith', 'type': 'Phantom', 'abilities': ['Ghost Message', 'Static Whisper', 'Memory Trace'], 'special': 'Vanishing Call', 'animation': 'mystic', 'mission': 'Recover the mysterious message before it disappears.'}}, 'chair': {'fantasy': {'name': 'Iron Throne Beast', 'type': 'Guardian', 'abilities': ['Royal Slam', 'Iron Guard', 'Throne Charge'], 'special': "King's Wrath", 'animation': 'earth', 'mission': 'Defeat the guardian of the enchanted throne.'}, 'action': {'name': 'Chair Crusher', 'type': 'Combat', 'abilities': ['Leg Strike', 'Seat Slam', 'Charge'], 'special': 'Furniture Fury', 'animation': 'impact', 'mission': 'Defeat the Chair Crusher before it blocks your escape.'}, 'sci-fi': {'name': 'Mecha Seat', 'type': 'Machine', 'abilities': ['Hydraulic Strike', 'Servo Dash', 'Metal Shield'], 'special': 'Overdrive', 'animation': 'energy', 'mission': 'Disable the Mecha Seat before its defense system activates.'}, 'mystery': {'name': 'Haunted Chair', 'type': 'Phantom', 'abilities': ['Silent Move', 'Ghost Grip', 'Shadow Sit'], 'special': 'Possession', 'animation': 'mystic', 'mission': 'Discover why the Haunted Chair moves on its own.'}}, 'plant': {'fantasy': {'name': 'Thornling', 'type': 'Nature', 'abilities': ['Vine Lash', 'Thorn Burst', 'Healing Leaf'], 'special': 'Ancient Bloom', 'animation': 'nature', 'mission': 'Protect the magical bloom from corruption.'}, 'action': {'name': 'Vine Beast', 'type': 'Nature', 'abilities': ['Vine Strike', 'Root Trap', 'Thorn Shot'], 'special': 'Wild Growth', 'animation': 'nature', 'mission': 'Escape the Root Trap and defeat the Vine Beast.'}, 'sci-fi': {'name': 'BioDrone', 'type': 'Bio-Tech', 'abilities': ['Toxic Seed', 'Root Laser', 'Bio Pulse'], 'special': 'Mutation Burst', 'animation': 'nature', 'mission': 'Stop the BioDrone before its mutation spreads.'}, 'mystery': {'name': 'Whisper Vine', 'type': 'Unknown', 'abilities': ['Leaf Whisper', 'Hidden Root', 'Shadow Bloom'], 'special': 'Memory Flower', 'animation': 'mystic', 'mission': 'Follow the Whisper Vine to uncover its secret.'}}, 'fan': {'fantasy': {'name': 'Windling', 'type': 'Air', 'abilities': ['Wind Slash', 'Air Spin', 'Gale Push'], 'special': 'Cyclone Crown', 'animation': 'wind', 'mission': 'Capture the runaway Windling before the magical storm grows.'}, 'action': {'name': 'Air Striker', 'type': 'Combat', 'abilities': ['Blade Wind', 'Dash', 'Air Shot'], 'special': 'Cyclone Strike', 'animation': 'wind', 'mission': 'Survive the Air Striker and reach extraction.'}, 'sci-fi': {'name': 'AeroDrone', 'type': 'Machine', 'abilities': ['Rotor Blast', 'Air Cannon', 'Turbo Dash'], 'special': 'Tornado Drive', 'animation': 'wind', 'mission': 'Disable the AeroDrone before it destabilizes the room.'}, 'mystery': {'name': 'Whisper Gale', 'type': 'Spectral', 'abilities': ['Cold Breeze', 'Whisper', 'False Wind'], 'special': 'Silent Storm', 'animation': 'wind', 'mission': 'Follow the strange wind to discover what happened.'}}, 'display': {'fantasy': {'name': 'Screen Oracle', 'type': 'Mystic', 'abilities': ['Mirror Beam', 'Vision Curse', 'Illusion Frame'], 'special': 'Infinite Reflection', 'animation': 'magic', 'mission': 'Read the prophecy hidden inside the Screen Oracle.'}, 'action': {'name': 'Display Raider', 'type': 'Combat', 'abilities': ['Screen Shot', 'Flash Strike', 'Target Lock'], 'special': 'Blinding Burst', 'animation': 'shooting', 'mission': 'Defeat the Display Raider before it activates security.'}, 'sci-fi': {'name': 'Screen Wraith', 'type': 'Cyber', 'abilities': ['Pixel Beam', 'Data Spike', 'Screen Warp'], 'special': 'Digital Collapse', 'animation': 'glitch', 'mission': 'Stop the Screen Wraith from taking control.'}, 'mystery': {'name': 'Mirror Watcher', 'type': 'Unknown', 'abilities': ['Clue Reveal', 'False Reflection', 'Memory Flash'], 'special': 'Truth Break', 'animation': 'mystic', 'mission': 'Discover what the Mirror Watcher is hiding.'}}}

    if object_key in creatures:
        result = creatures[object_key].get(
            genre_key,
            next(iter(creatures[object_key].values())),
        )

        print(f"REALITY OBJECT: {object_label}")
        print(f"GENRE: {genre_key}")
        print(f"GENERATED CREATURE: {result['name']}")

        return result

    return {
        "name": f"{str(object_label).title()} Beast",
        "type": "Reality",
        "abilities": [
            "Object Strike",
            "Reality Surge",
            "World Shift",
        ],
        "special": "Reality Break",
        "animation": "mystic",
        "mission": (
            f"Defeat the creature born from "
            f"the {object_label}."
        ),
    }
