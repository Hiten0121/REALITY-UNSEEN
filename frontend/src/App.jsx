import {
  useEffect,
  useRef,
  useState
} from "react";

import {
  analyzeFrame,
  gameAction,
  getStoryHistory,
  scanGameObjects,
  getStoryOptions,
  resetWorld,
  resumeStory,
  startStory
} from "./api";

import Auth from "./Auth.jsx";
import CartoonBattle from "./CartoonBattle";
import ObjectMission from "./ObjectMission.jsx";

import {
  getCurrentUser,
  listenToAuthChanges,
  signOut
} from "./auth.js";


function App() {

  // =========================================================
  // AUTHENTICATION
  // =========================================================

  const [user, setUser] =
    useState(null);

  const [authLoading, setAuthLoading] =
    useState(true);


  useEffect(() => {

    let mounted = true;


    async function loadUser() {

      const currentUser =
        await getCurrentUser();

      if (mounted) {

        setUser(currentUser);

        setAuthLoading(false);

      }

    }


    loadUser();


    const {
      data
    } = listenToAuthChanges(
      (currentUser) => {

        setUser(currentUser);

        setAuthLoading(false);

      }
    );


    return () => {

      mounted = false;

      data.subscription.unsubscribe();

    };

  }, []);


  // Load history after authentication is available.
  useEffect(() => {

    if (user) {
      loadHistory();
    }

  }, [user]);


  const videoRef =
    useRef(null);

  const canvasRef =
    useRef(null);


  const [cameraReady, setCameraReady] =
    useState(false);

  const [scene, setScene] =
    useState(null);

  const [stories, setStories] =
    useState([]);

  const [game, setGame] =
    useState(null);

  const [historyItems, setHistoryItems] =
    useState([]);

  const [mode, setMode] =
    useState("camera");

  const [busy, setBusy] =
    useState(false);

  const [message, setMessage] =
    useState(
      "Point the camera at your surroundings."
    );

  // Child-friendly accessibility controls.
  const [textScale, setTextScale] = useState("normal");
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [showDetectionBoxes, setShowDetectionBoxes] = useState(true);

  // Prevent repeated automatic mission initialization for the same story.
  const missionInitStoryRef = useRef(null);


  useEffect(() => {

    let stream;


    async function initializeCamera() {

      try {

        stream =
          await navigator.mediaDevices
            .getUserMedia({

              video: {

                facingMode:
                  {
                    ideal:
                      "environment"
                  },

                width:
                  {
                    ideal:
                      1280
                  },

                height:
                  {
                    ideal:
                      720
                  }

              },

              audio: false

            });


        videoRef.current.srcObject =
          stream;


        setCameraReady(
          true
        );


      } catch (error) {

        setMessage(
          `Camera error: ${error.message}`
        );

      }

    }


    initializeCamera();


    return () => {

      if (stream) {

        stream
          .getTracks()
          .forEach(
            track =>
              track.stop()
          );

      }

    };

  }, []);


  async function loadHistory() {

    try {

      const data =
        await getStoryHistory();

      setHistoryItems(
        data
      );

    } catch (error) {

      console.error(
        error
      );

    }

  }


  function captureFrame() {

    const video =
      videoRef.current;

    const canvas =
      canvasRef.current;


    if (!video || !canvas) {
      return null;
    }


    const sourceWidth =
      video.videoWidth ||
      960;

    const sourceHeight =
      video.videoHeight ||
      540;


    const width =
      Math.min(
        sourceWidth,
        960
      );


    const height =
      Math.round(
        width *
        sourceHeight /
        sourceWidth
      );


    canvas.width =
      width;

    canvas.height =
      height;


    const context =
      canvas.getContext(
        "2d"
      );


    context.drawImage(
      video,
      0,
      0,
      width,
      height
    );


    return canvas
      .toDataURL(
        "image/jpeg",
        0.72
      )
      .split(",")[1];

  }


  async function scanReality() {

    if (!cameraReady) {

      setMessage(
        "Camera is not ready."
      );

      return;

    }


    setBusy(true);

    setMessage(
      "Gemini is understanding your environment..."
    );


    try {

      const image =
        captureFrame();


      const detectedScene =
        await analyzeFrame(
          image
        );


      setScene(
        detectedScene
      );


      setMessage(
        "Environment understood. Creating multiple realities..."
      );


      const generatedStories =
        await getStoryOptions(
          detectedScene
        );


      setStories(
        generatedStories
      );


      setMode(
        "stories"
      );


      setMessage(
        "Choose the reality you want to enter."
      );


    } catch (error) {

      setMessage(
        error.message
      );

    } finally {

      setBusy(false);

    }

  }


  async function selectStory(
    story
  ) {

    if (!scene) {
      return;
    }


    setBusy(true);

    setMessage(
      "Creating your persistent story..."
    );


    try {

      const state =
        await startStory(
          story,
          scene
        );


      setGame(
        state
      );


      setMode(
        "game"
      );


      setMessage(
        "Story locked. AI will continue this story."
      );


      await loadHistory();


    } catch (error) {

      setMessage(
        error.message
      );

    } finally {

      setBusy(false);

    }

  }


  // =========================================================
  // SCAN CURRENT MISSION TARGETS
  // =========================================================
  async function scanForMissionTargets() {
    if (!game) {
      return;
    }

    if (!cameraReady) {
      setMessage("Camera is not ready.");
      return;
    }

    if (
      game.gameplay_type === "battle" ||
      game.object_mission?.completed
    ) {
      return;
    }

    setBusy(true);
    setMessage("Scanning reality for your mission targets...");

    try {
      const image = captureFrame();

      if (!image) {
        throw new Error("Could not capture a camera frame.");
      }

      const detectedScene = await analyzeFrame(image);

      setScene(detectedScene);

      // Let the backend perform the canonical target matching and
      // persist the updated mission state in the active game.
      const nextState = await scanGameObjects(detectedScene);

      setGame(nextState);

      setMessage(
        nextState.log?.at(-1) ||
        (nextState.object_mission?.completed
          ? "Mission complete. The story will evolve."
          : "Scan complete. Keep searching.")
      );

      await loadHistory();
    } catch (error) {
      console.error(error);
      setMessage(error?.message || "Mission scan failed.");
    } finally {
      setBusy(false);
    }
  }

  // Some existing/stale game states can reach the frontend without an
  // object_mission. Automatically perform one fresh camera scan so the
  // player does not get stuck on the empty "Scanning the world" screen.
  useEffect(() => {
    const storyId = game?.story?.story_id;

    if (
      mode !== "game" ||
      !game ||
      game.gameplay_type === "battle" ||
      game.object_mission ||
      !cameraReady ||
      !storyId ||
      missionInitStoryRef.current === storyId
    ) {
      return;
    }

    missionInitStoryRef.current = storyId;
    scanForMissionTargets();
  }, [mode, game?.story?.story_id, game?.gameplay_type, Boolean(game?.object_mission), cameraReady]);


  async function performAction(
    action
  ) {

    if (!game) {
      return;
    }


    setBusy(true);

    try {

      const nextState =
        await gameAction(
          action
        );


      setGame(
        nextState
      );


      setMessage(
        nextState.log.at(-1) ||
        "Action complete."
      );


      await loadHistory();


    } catch (error) {

      setMessage(
        error.message
      );

    } finally {

      setBusy(false);

    }

  }


  async function resumeSavedStory(
    storyId
  ) {

    setBusy(true);


    try {

      const state =
        await resumeStory(
          storyId
        );


      setGame(
        state
      );


      setMode(
        "game"
      );


      setMessage(
        "Saved story resumed. The AI will continue its existing narrative."
      );


    } catch (error) {

      setMessage(
        error.message
      );

    } finally {

      setBusy(false);

    }

  }


  async function newReality() {

    try {

      await resetWorld();

      setScene(null);

      setStories([]);

      setGame(null);

      setMode("camera");

      setMessage(
        "New reality ready."
      );

      await loadHistory();

    } catch (error) {

      setMessage(
        error.message
      );

    }

  }


  // =========================================================
  // AUTH LOADING
  // =========================================================

  if (authLoading) {

    return (
      <div className="loading-screen">
        LOADING REALITY...
      </div>
    );

  }


  // =========================================================
  // LOGIN / SIGN UP
  // =========================================================

  if (!user) {

    return (
      <Auth
        onLogin={(loggedInUser) => {

          setUser(loggedInUser);

        }}
      />
    );

  }


  const entities =
    game?.render_entities || [];

  const missionTargets = Array.isArray(game?.object_mission?.targets)
    ? game.object_mission.targets
    : [];

  function getObjectIcon(label = "") {
    const text = String(label).toLowerCase();
    if (text.includes("bottle")) return "🍼";
    if (text.includes("id") || text.includes("card") || text.includes("document")) return "🪪";
    if (text.includes("glass") || text.includes("spectacle") || text.includes("specs")) return "👓";
    if (text.includes("pen") || text.includes("pencil")) return "🖊️";
    if (text.includes("book") || text.includes("paper")) return "📖";
    if (text.includes("phone")) return "📱";
    if (text.includes("laptop") || text.includes("computer")) return "💻";
    if (text.includes("chair")) return "🪑";
    if (text.includes("bag") || text.includes("backpack")) return "🎒";
    if (text.includes("key")) return "🔑";
    if (text.includes("ball")) return "⚽";
    if (text.includes("plant") || text.includes("tree")) return "🌱";
    if (text.includes("car") || text.includes("vehicle")) return "🚗";
    return "🔎";
  }

  const showMissionCamera =
    mode === "game" &&
    game &&
    game.gameplay_type !== "battle";


  return (

    <main className="app">

      <video
        ref={videoRef}
        className={`camera ${
          mode === "game" && game?.gameplay_type === "battle"
            ? "camera-hidden"
            : ""
        }`}
        autoPlay
        muted
        playsInline
      />


      <canvas
        ref={canvasRef}
        hidden
      />


      <div className="camera-overlay" />

      {showMissionCamera &&
        showDetectionBoxes &&
        missionTargets.length > 0 && (
          <div
            className="mission-detection-layer"
            aria-label="AI object detection boxes"
            style={{
              position: "absolute",
              inset: 0,
              zIndex: 8,
              pointerEvents: "none",
              overflow: "hidden",
            }}
          >
            {missionTargets.map((target, index) => {
              const raw = Array.isArray(target?.bbox)
                ? target.bbox.map(Number)
                : [];

              /*
                Expected bbox format:
                [x, y, width, height]
                All values are normalized from 0 to 1.

                This makes the rectangle track the real object in
                the camera frame.
              */
              const valid =
                raw.length >= 4 &&
                raw.slice(0, 4).every(Number.isFinite) &&
                raw[2] > 0 &&
                raw[3] > 0;

              if (!valid) return null;

              const x = Math.max(0, Math.min(1, raw[0]));
              const y = Math.max(0, Math.min(1, raw[1]));
              const width = Math.max(
                0.02,
                Math.min(1 - x, raw[2])
              );
              const height = Math.max(
                0.02,
                Math.min(1 - y, raw[3])
              );

              const found = Boolean(target?.found);
              const icon = getObjectIcon(target?.label);
              const confidence =
                Number.isFinite(Number(target?.confidence))
                  ? Math.round(Number(target.confidence) * 100)
                  : null;

              return (
                <div
                  key={target?.id || `detection-${index}`}
                  className={`object-detection-box ${
                    found ? "object-detection-found" : ""
                  }`}
                  style={{
                    position: "absolute",
                    left: `${x * 100}%`,
                    top: `${y * 100}%`,
                    width: `${width * 100}%`,
                    height: `${height * 100}%`,
                    boxSizing: "border-box",
                    border: found
                      ? "3px solid #55f0b1"
                      : "3px solid #61d9ff",
                    borderRadius: "8px",
                    boxShadow: found
                      ? "0 0 20px rgba(85,240,177,.75)"
                      : "0 0 18px rgba(97,217,255,.55)",
                  }}
                >
                  {/* Animated corner brackets make the box easy for children to see. */}
                  <span className="detection-corner corner-tl" />
                  <span className="detection-corner corner-tr" />
                  <span className="detection-corner corner-bl" />
                  <span className="detection-corner corner-br" />

                  <div className="detection-label">
                    <span className="detection-icon">
                      {found ? "✅" : icon}
                    </span>

                    <span className="detection-name">
                      {target?.label || "OBJECT"}
                    </span>

                    {confidence !== null && (
                      <span className="detection-confidence">
                        {confidence}%
                      </span>
                    )}
                  </div>

                  <div className="detection-status">
                    {found ? "FOUND!" : "FIND ME"}
                  </div>
                </div>
              );
            })}
          </div>
        )}

      <header className="topbar">

        <div>

          <div className="brand">
            REALITY
            <span>:UNSEEN</span>
          </div>

          <div className="subtitle">
            AI-Generated Reality
          </div>

        </div>


        <div className="topbar-user">

          <div className="user-badge">
            {user?.user_metadata?.username ||
              user?.email}
          </div>

          <button
            className="logout-button"
            onClick={async () => {

              try {

                await signOut();

                setUser(null);
                setGame(null);
                setScene(null);
                setStories([]);
                setMode("camera");

              } catch (error) {

                setMessage(
                  error?.message ||
                  "Logout failed."
                );

              }

            }}
          >
            LOGOUT
          </button>

          <div className="camera-status">

            <span
              className={
                cameraReady
                  ? "status-dot active"
                  : "status-dot"
              }
            />

            {cameraReady
              ? "CAMERA LIVE"
              : "CAMERA OFF"}

          </div>

        </div>

      </header>


      <section
        className={`hud ${
          mode === "game" ? "hud-hidden" : ""
        }`}
      >

        <div className="world-card">

          <div className="eyebrow">
            WORLD PERCEPTION
          </div>

          <h2>
            {scene
              ? scene.environment
              : "UNSCANNED"}
          </h2>

          <p>
            {scene
              ? scene.summary
              : "Scan reality to begin."}
          </p>


          {scene && (

            <div className="chips">

              <span>
                {scene.objects.length}
                {" "}
                objects
              </span>

              <span>
                Crowd:
                {" "}
                {scene.crowd_density}
              </span>

            </div>

          )}

        </div>


        <div className="reticle">

          <div className="reticle-ring" />

          <div className="reticle-cross" />

        </div>


        <div className="story-card">

          <div className="eyebrow">
            ACTIVE STORY
          </div>


          {game ? (

            <>

              <h2>
                {game.story.title}
              </h2>

              <p>
                {game.story.current_event}
              </p>


              <div className="objective">

                <small>
                  CURRENT OBJECTIVE
                </small>

                <div>
                  {game.story.objective}
                </div>

              </div>

            </>

          ) : (

            <p>
              Your selected story will
              appear here.
            </p>

          )}

        </div>


        {entities.map(
          entity => (

            <div
              key={entity.id}
              className={
                entity.type === "enemy"
                  ? "entity enemy"
                  : "entity"
              }
              style={{
                left:
                  `${(
                    entity.bbox?.[0] ??
                    0.5
                  ) * 100}%`,

                top:
                  `${(
                    entity.bbox?.[1] ??
                    0.3
                  ) * 100}%`
              }}
            >

              <div className="entity-label">

                {entity.type === "enemy"
                  ? "⚠ "
                  : "◆ "}

                {entity.label}

              </div>

              <div className="entity-bracket" />

            </div>

          )
        )}

      </section>


      <section
        className={`bottom-ui ${
          mode === "game" && game?.gameplay_type === "battle"
            ? "bottom-ui-hidden"
            : ""
        }`}
      >

        <div className="message">

          {message}

        </div>


        {mode === "camera" && (

          <div className="action-row">

            <button
              className="primary"
              disabled={
                busy ||
                !cameraReady
              }
              onClick={
                scanReality
              }
            >

              {busy
                ? "ANALYZING..."
                : "SCAN REALITY"}

            </button>


            <button
              onClick={() =>
                setMode("history")
              }
            >
              STORY HISTORY
            </button>

          </div>

        )}


        {mode === "stories" && (

          <div className="panel">

            <div className="eyebrow">
              CHOOSE YOUR REALITY
            </div>

            <h2>
              Multiple stories detected
            </h2>


            <div className="story-grid">

              {stories.map(
                story => (

                  <article
                    className="story-option"
                    key={story.id}
                  >

                    <div className="genre">
                      {story.genre}
                      {" · "}
                      {story.tone}
                    </div>

                    <h3>
                      {story.title}
                    </h3>

                    <p>
                      {story.premise}
                    </p>

                    <div className="mission">
                      MISSION
                      <br />
                      {story.objective}
                    </div>

                    <button
                      disabled={busy}
                      onClick={() =>
                        selectStory(
                          story
                        )
                      }
                    >
                      ENTER STORY
                    </button>

                  </article>

                )
              )}

            </div>


            <button
              onClick={() =>
                setMode("camera")
              }
            >
              BACK
            </button>

          </div>

        )}


        {/* =========================================================
            CARTOON AI BATTLE
        ========================================================= */}

        {mode === "game" && game && (
          game.gameplay_type === "battle" ? (
            <CartoonBattle
              game={game}
              onAction={performAction}
              onScan={scanReality}
            />
          ) : (
            <ObjectMission
              mission={game.object_mission}
              onScan={scanForMissionTargets}
              busy={busy}
              textScale={textScale}
              onTextScaleChange={setTextScale}
              voiceEnabled={voiceEnabled}
              onVoiceEnabledChange={setVoiceEnabled}
              showDetectionBoxes={showDetectionBoxes}
              onDetectionBoxesChange={setShowDetectionBoxes}
            />
          )
        )}


        {mode === "history" && (

          <div className="panel history-panel">

            <div className="history-header">

              <div>

                <div className="eyebrow">
                  CANONICAL STORY ARCHIVE
                </div>

                <h2>
                  Your Realities
                </h2>

              </div>


              <button
                onClick={() =>
                  setMode(
                    game
                      ? "game"
                      : "camera"
                  )
                }
              >
                CLOSE
              </button>

            </div>


            {historyItems.length === 0 && (

              <p>
                No stories saved yet.
              </p>

            )}


            <div className="history-list">

              {historyItems.map(
                item => (

                  <article
                    className="history-item"
                    key={
                      item.story.story_id
                    }
                  >

                    <div>

                      <div className="genre">

                        {item.story.genre}

                        {" · Chapter "}

                        {item.story.chapter}

                      </div>

                      <h3>
                        {item.story.title}
                      </h3>

                      <p>
                        {item.story.premise}
                      </p>

                      <small>
                        {
                          item.versions.length
                        }
                        {" "}
                        saved story events
                      </small>

                    </div>


                    <button
                      disabled={busy}
                      onClick={() =>
                        resumeSavedStory(
                          item.story.story_id
                        )
                      }
                    >
                      RESUME
                    </button>

                  </article>

                )
              )}

            </div>

          </div>

        )}

      </section>


      <div className="corner-controls">

        <button
          onClick={
            newReality
          }
        >
          NEW REALITY
        </button>

        <button
          onClick={() =>
            setMode("history")
          }
        >
          HISTORY
        </button>

      </div>

    </main>
  );
}


export default App;