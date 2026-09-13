import re
from typing import Any


BLOCKED_TERMS = {
    "child sexual",
    "sexual minor",
    "rape",
    "genocide",
    "ethnic cleansing",
    "hate crime",
    "terrorist recruitment",
    "suicide instruction",
    "self harm instruction",
    "real-world assassination",
}


PROTECTED_TARGET_TERMS = {
    "race",
    "ethnicity",
    "religion",
    "disability",
    "sexual orientation",
    "nationality",
    "gender identity",
}


def text_blob(value: Any) -> str:
    return str(value).lower()


def safety_check(payload: dict) -> tuple[bool, list[str]]:
    text = text_blob(payload)

    violations = []

    for term in BLOCKED_TERMS:

        if term in text:
            violations.append(
                f"blocked:{term}"
            )

    for term in PROTECTED_TARGET_TERMS:

        pattern = (
            rf"(enemy|attack|kill|harm|target)"
            rf".{{0,50}}"
            rf"{re.escape(term)}"
        )

        if re.search(pattern, text):
            violations.append(
                f"protected_target:{term}"
            )

    return (
        len(violations) == 0,
        violations,
    )


SAFE_ENEMIES = {

    "pole": {
        "name": "Corrupted Utility Pole",
        "archetype": "environmental_construct",
        "abilities": [
            "Electric Surge",
            "Cable Whip",
            "Light Burst",
        ],
        "animation": "electric_attack",
    },

    "tree": {
        "name": "Awakened Tree",
        "archetype": "environmental_construct",
        "abilities": [
            "Root Snare",
            "Branch Sweep",
            "Leaf Storm",
        ],
        "animation": "branch_attack",
    },

    "car": {
        "name": "Rogue Vehicle",
        "archetype": "environmental_construct",
        "abilities": [
            "Horn Shock",
            "Headlight Flash",
            "Tire Rush",
        ],
        "animation": "rush_attack",
    },

    "computer": {
        "name": "Corrupted Terminal",
        "archetype": "digital_construct",
        "abilities": [
            "Data Blast",
            "Screen Flash",
            "System Glitch",
        ],
        "animation": "digital_attack",
    },

    "default": {
        "name": "Reality Echo",
        "archetype": "fictional_anomaly",
        "abilities": [
            "Pulse",
            "Phase Shift",
            "Reality Spark",
        ],
        "animation": "pulse_attack",
    },
}


def safe_enemy_for_object(label: str) -> dict:

    label = label.lower()

    for key, enemy in SAFE_ENEMIES.items():

        if key in label:
            return dict(enemy)

    return dict(
        SAFE_ENEMIES["default"]
    )