import base64
import json

from google import genai
from google.genai import types

from app.config import get_settings
from app.schemas import SceneModel


settings = get_settings()


# ============================================================
# GEMINI RESPONSE SCHEMA
# ============================================================

SCENE_SCHEMA = {
    "type": "object",

    "properties": {

        # ----------------------------------------------------
        # Environment
        # ----------------------------------------------------

        "environment": {
            "type": "string"
        },

        "summary": {
            "type": "string"
        },

        "crowd_density": {
            "type": "string",
            "enum": [
                "none",
                "low",
                "medium",
                "high",
            ],
        },

        # ----------------------------------------------------
        # Player
        # ----------------------------------------------------

        "player_visible": {
            "type": "boolean"
        },

        # IMPORTANT:
        # Do NOT use:
        #
        # "type": ["array", "null"]
        #
        # Gemini's schema validator rejects that format.
        #
        # Always return an object.
        #
        # If the player is not visible, Gemini should return
        # zero values.
        # ----------------------------------------------------

        "player_bbox": {
            "type": "object",

            "properties": {

                "x": {
                    "type": "number"
                },

                "y": {
                    "type": "number"
                },

                "width": {
                    "type": "number"
                },

                "height": {
                    "type": "number"
                },
            },

            "required": [
                "x",
                "y",
                "width",
                "height",
            ],
        },

        # ----------------------------------------------------
        # Detected objects
        # ----------------------------------------------------

        "objects": {
            "type": "array",

            "items": {
                "type": "object",

                "properties": {

                    "id": {
                        "type": "string"
                    },

                    "label": {
                        "type": "string"
                    },

                    "category": {
                        "type": "string"
                    },

                    "confidence": {
                        "type": "number"
                    },

                    "bbox": {
                        "type": "array",

                        "items": {
                            "type": "number"
                        },
                    },

                    "story_relevance": {
                        "type": "number"
                    },
                },

                "required": [
                    "id",
                    "label",
                    "category",
                    "confidence",
                    "bbox",
                    "story_relevance",
                ],
            },
        },
    },

    "required": [
        "environment",
        "summary",
        "crowd_density",
        "player_visible",
        "player_bbox",
        "objects",
    ],
}


# ============================================================
# FRAME ANALYSIS
# ============================================================

def analyze_frame(
    image_base64: str,
    mime_type: str,
) -> SceneModel:

    # --------------------------------------------------------
    # Check Gemini API key
    # --------------------------------------------------------

    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing"
        )

    # --------------------------------------------------------
    # Create Gemini client
    # --------------------------------------------------------

    client = genai.Client(
        api_key=settings.gemini_api_key
    )

    # --------------------------------------------------------
    # Decode camera image
    # --------------------------------------------------------

    try:
        image_bytes = base64.b64decode(
            image_base64
        )
    except Exception as exc:
        raise RuntimeError(
            "Invalid base64 image data"
        ) from exc

    # --------------------------------------------------------
    # Vision prompt
    # --------------------------------------------------------

    prompt = """
You are the perception engine for a fictional
single-player game called REALITY: UNSEEN.

Analyze the entire camera frame.

Detect useful environmental information such as:

- buildings
- roads
- trees
- poles
- vehicles
- furniture
- signs
- objects
- animals
- groups/crowds

IMPORTANT:

Do not identify people.

Do not infer:

- race
- ethnicity
- religion
- political affiliation
- disability
- sexual orientation
- gender identity
- private information

For crowded environments, DO NOT create one object
for every person.

Instead represent the group as:

crowd

with its approximate density.

--------------------------------------------------
BOUNDING BOX FORMAT
--------------------------------------------------

For detected environmental objects, return:

[x, y, width, height]

Every value must be normalized between 0 and 1.

Example:

[0.10, 0.20, 0.30, 0.40]

--------------------------------------------------
PLAYER BOUNDING BOX
--------------------------------------------------

player_bbox MUST be an object:

{
    "x": 0.10,
    "y": 0.20,
    "width": 0.30,
    "height": 0.40
}

Every player_bbox value must be between 0 and 1.

If the player is not visible, return:

{
    "x": 0,
    "y": 0,
    "width": 0,
    "height": 0
}

and set:

"player_visible": false

If the player is visible, set:

"player_visible": true

and provide the normalized bounding box.

--------------------------------------------------
STORY RELEVANCE
--------------------------------------------------

story_relevance is only an initial estimate.

The story engine will later decide which objects
become game entities.

The game should understand the entire environment
but only render story-relevant entities.

Return only the requested JSON structure.
"""

    # --------------------------------------------------------
    # Gemini request
    # --------------------------------------------------------

    response = client.models.generate_content(

        model=settings.gemini_model,

        contents=[
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type,
            ),

            prompt,
        ],

        config=types.GenerateContentConfig(

            response_mime_type="application/json",

            response_schema=SCENE_SCHEMA,

            temperature=0.1,
        ),
    )

    # --------------------------------------------------------
    # Parse Gemini response
    # --------------------------------------------------------

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty response"
        )

    try:
        data = json.loads(
            response.text
        )
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Gemini returned invalid JSON"
        ) from exc

    # --------------------------------------------------------
    # Validate against our application schema
    # --------------------------------------------------------

    try:
        scene = SceneModel.model_validate(
            data
        )
    except Exception as exc:
        raise RuntimeError(
            f"Gemini returned invalid scene data: {exc}"
        ) from exc

    return scene