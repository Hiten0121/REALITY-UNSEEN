# REALITY: UNSEEN

REALITY: UNSEEN is a web-based AI game that transforms the player's real-world camera environment into a dynamic fictional game.

The player points a camera at the environment.

AI understands the environment.

The game generates multiple possible stories.

The player selects one.

That story becomes canonical.

The AI Game Director then adapts that SAME story according to the player's gameplay.

---

## Core Pipeline

Camera

↓

Gemini Vision

↓

World Model

↓

Multiple Story Generator

↓

Player Selects Story

↓

Canonical Story

↓

Game Engine

↓

Player Gameplay

↓

AI Game Director

↓

Story Adaptation

↓

Next Chapter / Event

---

## Important Story Rule

The game does NOT create a completely new story every time the player struggles.

Example:

Story:

"The Silent District"

Chapter 1:

Find the communication device.

Player struggles.

Chapter 2:

A hidden route is discovered.

Player continues.

Chapter 3:

The enemy becomes stronger.

The story remains "The Silent District".

Every important story change is stored in the story history.

---

## AI Providers

### Gemini

Used for:

- camera vision
- environment detection
- object detection
- crowd understanding
- bounding boxes

### Groq

Used for:

- story generation
- multiple story generation
- AI Game Director
- adaptive missions
- enemy suggestions

### Ollama

Used for:

- local AI experiments
- local reasoning
- future offline mode

---

## Crowd Optimization

The AI can understand a crowded environment without creating hundreds of game entities.

For example:

100 people

may become:

{
    "type": "crowd",
    "count": 100
}

The game can visually represent the crowd with lightweight proxies.

Only important story characters become full game entities.

This reduces rendering and AI load.

---

## Story-Relevance System

Each detected object receives:

story_relevance

0 - 100

Objects with high relevance can become:

- quest objects
- enemies
- NPCs
- objectives

Low relevance objects remain environmental information.

---

## Example

Camera detects:

- tree
- pole
- road
- building
- 40 people
- cars

AI creates:

Story:

"The city's infrastructure has awakened."

Enemy:

"Corrupted Utility Pole"

Abilities:

- Electric Surge
- Cable Whip
- Light Burst

The pole becomes the enemy because it exists in the player's real environment.

---

## Combat

Combat is turn-based.

Actions:

ATTACK

REALITY SHIFT

DEFEND

SCAN

The backend controls the rules.

The frontend controls the visual experience.

---

## Adaptive Difficulty

The AI Game Director monitors gameplay.

If the player struggles:

- easier objective
- clues
- alternate route
- weaker enemy
- additional help

If the player performs extremely well:

- stronger fictional enemy
- harder objective
- additional story complication

These changes are expressed as story events instead of exposing internal difficulty numbers to the player.

---

# Installation

## Backend

Open terminal:

cd backend

Create environment:

python -m venv .venv

Activate on Windows:

.venv\Scripts\activate

Install:

pip install -r requirements.txt

Copy:

.env.example

to:

.env

Add:

GEMINI_API_KEY=...

GROQ_API_KEY=...

---

# Ollama

Install Ollama.

Then:

ollama pull gemma3

Start Ollama:

ollama serve

---

# Start backend

From backend:

uvicorn app.main:app --reload --port 8000

Test:

http://127.0.0.1:8000/api/health

---

# Frontend

Open another terminal:

cd frontend

Install:

npm install

Start:

npm run dev

Open:

http://localhost:5173

---

# Camera

The browser will ask for camera permission.

Allow camera access.

Press:

SCAN REALITY

---

# GitHub

Initialize:

git init

Add files:

git add .

Commit:

git commit -m "Initial REALITY UNSEEN"

Create a GitHub repository and then:

git remote add origin YOUR_REPOSITORY_URL

git branch -M main

git push -u origin main

Never commit:

.env

The .gitignore file already excludes it.

---

# API Endpoints

GET /api/health

POST /api/world/analyze-frame

POST /api/story/options

POST /api/story/start

GET /api/game/state

POST /api/game/action

POST /api/story/adapt

GET /api/story/history

GET /api/story/history/{story_id}

POST /api/story/resume/{story_id}

POST /api/world/reset