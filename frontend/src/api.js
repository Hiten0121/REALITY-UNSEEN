import { supabase } from "./supabase.js";

const API = import.meta.env.VITE_API_URL;

async function request(endpoint, options = {}) {
  // Get the currently logged-in Supabase session
  const {
    data: { session },
    error: sessionError
  } = await supabase.auth.getSession();

  if (sessionError) {
    throw new Error("Unable to get authentication session.");
  }

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };

  // Attach Supabase JWT to FastAPI
  if (session?.access_token) {
    headers.Authorization = `Bearer ${session.access_token}`;
  }

  const response = await fetch(`${API}${endpoint}`, {
    ...options,
    headers
  });

  if (!response.ok) {
    let message = `Request failed: ${response.status}`;

    try {
      const error = await response.json();
      message = error.detail || message;
    } catch {
      // Keep the default error message
    }

    throw new Error(message);
  }

  return response.json();
}


// ===============================
// WORLD
// ===============================

export function analyzeFrame(
  image_base64,
  mime_type = "image/jpeg"
) {
  return request("/api/world/analyze-frame", {
    method: "POST",
    body: JSON.stringify({
      image_base64,
      mime_type
    })
  });
}

export function resetWorld() {
  return request("/api/world/reset", {
    method: "POST"
  });
}


// ===============================
// STORIES
// ===============================

export function getStoryOptions(scene) {
  return request("/api/story/options", {
    method: "POST",
    body: JSON.stringify(scene)
  });
}

export function startStory(story, scene) {
  return request("/api/story/start", {
    method: "POST",
    body: JSON.stringify({
      story,
      scene
    })
  });
}

export function getStoryHistory() {
  return request("/api/story/history", {
    method: "GET"
  });
}

export function getStoryHistoryById(story_id) {
  return request(`/api/story/history/${story_id}`, {
    method: "GET"
  });
}

export function resumeStory(story_id) {
  return request(`/api/story/resume/${story_id}`, {
    method: "POST"
  });
}


// ===============================
// GAME
// ===============================

export function getGameState() {
  return request("/api/game/state", {
    method: "GET"
  });
}

export function gameAction(action, target_id = null) {
  return request("/api/game/action", {
    method: "POST",
    body: JSON.stringify({
      action,
      target_id
    })
  });
}


// ===============================
// OBJECT / MISSION SCANNING
// ===============================

export function scanGameObjects(scene) {
  return request("/api/game/scan", {
    method: "POST",
    body: JSON.stringify(scene)
  });
}


// ===============================
// STORY ADAPTATION
// ===============================

export function adaptStory(payload) {
  return request("/api/story/adapt", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
