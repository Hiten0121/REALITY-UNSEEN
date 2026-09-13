import React, { useEffect, useMemo, useRef } from "react";
import "./ObjectMission.css";

const ICONS = [
  ["bottle", "🍼"],
  ["id", "🪪"],
  ["card", "🪪"],
  ["document", "📄"],
  ["glass", "👓"],
  ["spectacle", "👓"],
  ["specs", "👓"],
  ["pen", "🖊️"],
  ["pencil", "✏️"],
  ["paper", "📄"],
  ["book", "📖"],
  ["phone", "📱"],
  ["laptop", "💻"],
  ["computer", "💻"],
  ["chair", "🪑"],
  ["bag", "🎒"],
  ["backpack", "🎒"],
  ["key", "🔑"],
  ["ball", "⚽"],
  ["plant", "🌱"],
  ["tree", "🌳"],
  ["car", "🚗"],
  ["vehicle", "🚗"],
];

function getIcon(label = "") {
  const text = String(label).toLowerCase();
  const match = ICONS.find(([word]) => text.includes(word));
  return match?.[1] || "🔎";
}

function missionSpeech(mission, targets, completed) {
  if (!mission) return "";

  if (completed) {
    return `Mission complete. You found all ${targets.length} objects.`;
  }

  const names = targets
    .filter((target) => !target?.found)
    .map((target) => target?.label)
    .filter(Boolean);

  if (names.length === 0) return "Mission complete.";

  return `Mission. Find ${names.join(", ")}.`;
}

function buildScreenText(
  mission,
  targets,
  completed,
  foundCount,
  total,
  detectionEnabled
) {
  return [
    mission?.title ? `Mission: ${mission.title}` : "",
    mission?.description ? `Goal: ${mission.description}` : "",
    `Progress: ${foundCount} of ${total} found`,
    ...targets.map(
      (target, index) =>
        `${index + 1}. ${target?.label || "Unknown object"} — ${
          target?.found ? "FOUND" : "SEARCH"
        }${target?.description ? `. ${target.description}` : ""}`
    ),
    completed
      ? "Mission complete! Every required target has been found."
      : "Hint: Point the camera at an object and scan it.",
    detectionEnabled
      ? "Object detection boxes are ON. Look for the square around the target."
      : "Object detection boxes are OFF.",
  ].filter(Boolean);
}

export default function ObjectMission({
  mission,
  onScan,
  busy = false,
  textScale = "normal",
  onTextScaleChange,
  voiceEnabled = true,
  onVoiceEnabledChange,
  showDetectionBoxes = true,
  onDetectionBoxesChange,
}) {
  const lastSpokenRef = useRef("");

  const targets = Array.isArray(mission?.targets) ? mission.targets : [];

  const foundCount =
    typeof mission?.progress === "number"
      ? mission.progress
      : targets.filter((target) => target?.found).length;

  const total =
    typeof mission?.total === "number" && mission.total > 0
      ? mission.total
      : targets.length;

  const safeProgress = Math.min(
    Math.max(foundCount, 0),
    Math.max(total, 0)
  );

  const progressPercent =
    total > 0 ? Math.round((safeProgress / total) * 100) : 0;

  const completed =
    Boolean(mission?.completed) ||
    (total > 0 && safeProgress >= total);

  const detectionEnabled = showDetectionBoxes !== false;

  const speechText = useMemo(
    () => missionSpeech(mission, targets, completed),
    [mission, targets, completed]
  );

  const screenText = useMemo(
    () =>
      buildScreenText(
        mission,
        targets,
        completed,
        safeProgress,
        total,
        detectionEnabled
      ),
    [
      mission,
      targets,
      completed,
      safeProgress,
      total,
      detectionEnabled,
    ]
  );

  useEffect(() => {
    if (!voiceEnabled || !speechText) return;
    if (!("speechSynthesis" in window)) return;
    if (lastSpokenRef.current === speechText) return;

    lastSpokenRef.current = speechText;
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(speechText);
    utterance.rate = 0.9;
    utterance.pitch = 1.05;
    window.speechSynthesis.speak(utterance);
  }, [speechText, voiceEnabled]);

  function speakMission() {
    if (!speechText || !("speechSynthesis" in window)) return;

    lastSpokenRef.current = speechText;
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(speechText);
    utterance.rate = 0.9;
    utterance.pitch = 1.05;
    window.speechSynthesis.speak(utterance);
  }

  function stopSpeaking() {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
  }

  function changeTextSize(value) {
    onTextScaleChange?.(value);
  }

  function showTextList() {
    const message = screenText.join("\n");
    if (typeof window !== "undefined") {
      window.alert(`TEXT ON SCREEN\n\n${message}`);
    }
  }

  if (!mission) {
    return (
      <section
        className={`object-mission object-mission-empty mission-text-${textScale}`}
      >
        <div className="mission-glow" />
        <div className="mission-icon">◉</div>
        <p className="mission-eyebrow">REALITY MISSION</p>
        <h2>{busy ? "Scanning the world..." : "Mission needs a scan"}</h2>
        <p className="mission-description">
          {busy
            ? "The AI is deciding what you need to discover in your surroundings."
            : "Scan your surroundings to create a learning mission."}
        </p>

        <div className="accessibility-toolbar">
          <div className="text-size-controls">
            <span className="accessibility-label">TEXT</span>
            <button type="button" onClick={() => changeTextSize("small")}>A−</button>
            <button type="button" onClick={() => changeTextSize("normal")}>A</button>
            <button type="button" onClick={() => changeTextSize("large")}>A+</button>
            <button type="button" onClick={() => changeTextSize("xlarge")}>A++</button>
          </div>

          <div className="voice-controls">
            <button type="button" onClick={speakMission}>🔊 READ</button>
            <button type="button" onClick={stopSpeaking}>■ STOP</button>
            <button
              type="button"
              className={voiceEnabled ? "voice-on" : ""}
              onClick={() => onVoiceEnabledChange?.(!voiceEnabled)}
            >
              {voiceEnabled ? "🔈 VOICE ON" : "🔇 VOICE OFF"}
            </button>
          </div>

          <button type="button" className="list-text-button" onClick={showTextList}>
            ☰ LIST TEXT
          </button>
          <button
            type="button"
            className={`detection-toggle ${detectionEnabled ? "detection-on" : ""}`}
            onClick={() => onDetectionBoxesChange?.(!detectionEnabled)}
            aria-pressed={detectionEnabled}
            title="Show or hide the square object detection boxes"
          >
            {detectionEnabled ? "▣ BOXES ON" : "□ BOXES OFF"}
          </button>
        </div>

        <button
          className="mission-scan-button"
          onClick={onScan}
          disabled={busy}
        >
          {busy ? "SCANNING..." : "INITIALIZE MISSION"}
        </button>
      </section>
    );
  }

  const missionType = String(
    mission.mission_type || "hunt"
  ).toUpperCase();

  return (
    <section
      className={`object-mission mission-text-${textScale} ${
        completed ? "mission-complete" : ""
      }`}
    >
      <div className="mission-grid" />
      <div className="mission-glow" />

      <header className="mission-header">
        <div>
          <p className="mission-eyebrow">
            {missionType} // AI LEARNING MISSION
          </p>
          <h2>{mission.title || "Reality Learning Quest"}</h2>
          <p className="mission-description">
            {mission.description ||
              "Find the objects the AI has selected from your environment."}
          </p>
        </div>

        <div className="mission-status">
          {completed ? "COMPLETE" : "ACTIVE"}
        </div>
      </header>

      <div
        className="accessibility-toolbar"
        aria-label="Mission accessibility and reading controls"
      >
        <div className="text-size-controls">
          <span className="accessibility-label">TEXT</span>

          <button
            type="button"
            className={textScale === "small" ? "active" : ""}
            onClick={() => changeTextSize("small")}
            aria-label="Small text"
          >
            A−
          </button>

          <button
            type="button"
            className={textScale === "normal" ? "active" : ""}
            onClick={() => changeTextSize("normal")}
            aria-label="Normal text"
          >
            A
          </button>

          <button
            type="button"
            className={textScale === "large" ? "active" : ""}
            onClick={() => changeTextSize("large")}
            aria-label="Large text"
          >
            A+
          </button>

          <button
            type="button"
            className={textScale === "xlarge" ? "active" : ""}
            onClick={() => changeTextSize("xlarge")}
            aria-label="Extra large text"
          >
            A++
          </button>
        </div>

        <div className="voice-controls">
          <button
            type="button"
            onClick={speakMission}
            disabled={!("speechSynthesis" in window)}
            title="Read the mission aloud"
          >
            🔊 READ
          </button>

          <button
            type="button"
            onClick={stopSpeaking}
            disabled={!("speechSynthesis" in window)}
            title="Stop voice guidance"
          >
            ■ STOP
          </button>

          <button
            type="button"
            className={voiceEnabled ? "voice-on" : ""}
            onClick={() => onVoiceEnabledChange?.(!voiceEnabled)}
            title="Toggle automatic voice guidance"
          >
            {voiceEnabled ? "🔈 VOICE ON" : "🔇 VOICE OFF"}
          </button>
        </div>

        <button
          type="button"
          className="list-text-button"
          onClick={showTextList}
          title="Show all important text on this screen"
        >
          ☰ LIST TEXT
        </button>

        <button
          type="button"
          className={`detection-toggle ${
            detectionEnabled ? "detection-on" : ""
          }`}
          onClick={() =>
            onDetectionBoxesChange?.(!detectionEnabled)
          }
          aria-pressed={detectionEnabled}
          title="Show or hide the square object detection boxes"
        >
          {detectionEnabled ? "▣ BOXES ON" : "□ BOXES OFF"}
        </button>
      </div>

      <div className="mission-progress-section">
        <div className="mission-progress-label">
          <span>REALITY MATCH</span>
          <strong>
            {safeProgress} / {total}
          </strong>
        </div>

        <div className="mission-progress-track">
          <div
            className="mission-progress-fill"
            style={{ width: `${progressPercent}%` }}
          />
        </div>

        <div className="mission-progress-percent">
          {progressPercent}% detected
        </div>
      </div>

      <div className="mission-targets">
        {targets.length === 0 ? (
          <div className="mission-no-targets">
            <span>◎</span>
            <p>
              No targets have been selected yet. Scan the environment to
              continue.
            </p>
          </div>
        ) : (
          targets.map((target, index) => {
            const found = Boolean(target?.found);
            const icon = getIcon(target?.label);

            return (
              <article
                className={`mission-target ${found ? "target-found" : ""}`}
                key={target?.id || `target-${index}`}
              >
                <div className="target-icon" aria-hidden="true">
                  {found ? "✅" : icon}
                </div>

                <div className="target-index">
                  {found ? "✓" : String(index + 1).padStart(2, "0")}
                </div>

                <div className="target-content">
                  <div className="target-title-row">
                    <h3>{target?.label || "Unknown object"}</h3>
                    <span className="target-state">
                      {found ? "FOUND" : "SEARCH"}
                    </span>
                  </div>

                  {target?.description && <p>{target.description}</p>}
                </div>
              </article>
            );
          })
        )}
      </div>

      <div className="mission-visual-help">
        <span className="visual-help-icon">👀</span>
        <div>
          <strong>Look for the symbols on the camera</strong>
          <p>
            Unfound targets are highlighted with a square detection box
            on the camera. When the AI recognizes one, it changes to ✅ FOUND.
          </p>
        </div>
      </div>

      <footer className="mission-footer">
        {completed ? (
          <div className="mission-complete-message">
            <span>🎉</span>
            <div>
              <strong>Mission complete!</strong>
              <p>
                Every required target has been found. The AI can now evolve
                the story.
              </p>
            </div>
          </div>
        ) : (
          <>
            <div className="mission-hint">
              <span>💡</span>
              <p>
                Point the camera at an object and scan. The AI will verify
                whether it matches a target.
              </p>
            </div>

            <button
              type="button"
              className="mission-scan-button"
              onClick={onScan}
              disabled={busy || !onScan}
            >
              <span className="scan-button-icon">
                {busy ? "…" : "◉"}
              </span>
              <span>{busy ? "ANALYZING..." : "SCAN REALITY"}</span>
            </button>
          </>
        )}
      </footer>
    </section>
  );
}
