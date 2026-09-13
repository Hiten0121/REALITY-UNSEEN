import React, { useEffect, useState } from "react";
import "./CartoonBattle.css";

export default function CartoonBattle({
  game,
  onAction,
  onScan,
}) {
  const [animation, setAnimation] = useState("idle");
  const [message, setMessage] = useState("");

  const enemy = game?.enemy;

  /*
   * When a new enemy appears:
   *
   * transform
   *     ↓
   * entrance
   *     ↓
   * idle
   */
  useEffect(() => {
    if (!enemy) return;

    setAnimation("transform");
    setMessage(
      `${enemy.source_object || "Object"} is transforming...`
    );

    const transformTimer = setTimeout(() => {
      setAnimation("entrance");

      setMessage(
        `⚡ ${enemy.name} appeared!`
      );
    }, 2200);

    const idleTimer = setTimeout(() => {
      setAnimation("idle");
      setMessage(
        `${enemy.name} is ready for battle!`
      );
    }, 3400);

    return () => {
      clearTimeout(transformTimer);
      clearTimeout(idleTimer);
    };
  }, [enemy?.id]);

  /*
   * React to animation_state coming from
   * the Python game engine.
   */
  useEffect(() => {
    if (!enemy?.animation_state) return;

    const state = enemy.animation_state;

    if (state === "transform") {
      setAnimation("transform");
      return;
    }

    if (state === "hit") {
      setAnimation("hit");

      const timer = setTimeout(() => {
        setAnimation("idle");
      }, 700);

      return () => clearTimeout(timer);
    }

    if (state === "attack") {
      setAnimation("enemy-attack");

      const timer = setTimeout(() => {
        setAnimation("idle");
      }, 900);

      return () => clearTimeout(timer);
    }

    if (state === "special") {
      setAnimation("special");

      const timer = setTimeout(() => {
        setAnimation("idle");
      }, 1200);

      return () => clearTimeout(timer);
    }

    if (state === "defeat") {
      setAnimation("defeat");
      setMessage(
        `🏆 ${enemy.name} has been defeated!`
      );
      return;
    }

    if (state === "victory") {
      setAnimation("victory");
      return;
    }

    if (state === "scan") {
      setAnimation("scan");
      setMessage(
        `🔎 ${enemy.name}: ${enemy.type || "Unknown"} creature`
      );

      const timer = setTimeout(() => {
        setAnimation("idle");
      }, 1000);

      return () => clearTimeout(timer);
    }

    setAnimation("idle");
  }, [enemy?.animation_state]);

  if (!game) {
    return (
      <div className="battle-empty">
        <div className="loading-orb">✦</div>

        <h2>
          REALITY IS LOADING...
        </h2>

        <p>
          Preparing your AI-generated world.
        </p>
      </div>
    );
  }

  if (!enemy) {
    return (
      <div className="battle-empty">
        <div className="loading-orb">
          ✦
        </div>

        <h2>
          REALITY IS SHIFTING...
        </h2>

        <p>
          Searching your environment for
          something interesting...
        </p>
      </div>
    );
  }

  const playerHp = Math.max(
    0,
    Math.min(
      100,
      game.player_hp ?? 100
    )
  );

  const enemyMaxHp =
    enemy.max_hp || 100;

  const currentEnemyHp =
    game.enemy_hp ??
    enemy.hp ??
    enemyMaxHp;

  const enemyHpPercent = Math.max(
    0,
    Math.min(
      100,
      (currentEnemyHp / enemyMaxHp) * 100
    )
  );

  async function handleAction(action) {
    if (
      animation === "transform" ||
      animation === "entrance"
    ) {
      return;
    }

    if (game.battle_over) {
      setMessage(
        "The battle has ended."
      );
      return;
    }

    /*
     * Local visual animation.
     */
    if (action === "attack") {
      setAnimation("player-attack");
      setMessage(
        "⚔️ REALITY STRIKE!"
      );
    }

    if (action === "special") {
      setAnimation("player-special");
      setMessage(
        `✨ ${enemy.special || "REALITY SHIFT"}!`
      );
    }

    if (action === "defend") {
      setAnimation("player-defend");
      setMessage(
        "🛡️ Reality Shield activated!"
      );
    }

    if (action === "scan") {
      setAnimation("scan");
      setMessage(
        `🔎 Scanning ${enemy.source_object || "target"}...`
      );

      if (onScan) {
        await onScan();
      }

      return;
    }

    /*
     * Call the existing backend.
     */
    if (onAction) {
      await onAction(action);
    }
  }

  return (
    <div className="cartoon-battle">

      {/* =========================================
          HEADER
      ========================================== */}

      <div className="battle-header">

        <div className="header-story">

          <span className="ai-label">
            ✦ AI GENERATED ADVENTURE
          </span>

          <h2>
            {game.story?.title ||
              "REALITY: UNSEEN"}
          </h2>

          <p>
            {game.story?.objective ||
              "Survive the reality shift."}
          </p>

        </div>

        <div className="chapter-badge">
          CHAPTER{" "}
          {game.story?.chapter || 1}
        </div>

      </div>


      {/* =========================================
          STORY EVENT
      ========================================== */}

      {game.story?.current_event && (
        <div className="ai-event-box">

          <div className="ai-event-title">
            ✦ AI GAME DIRECTOR
          </div>

          <div className="ai-event-text">
            {game.story.current_event}
          </div>

        </div>
      )}


      {/* =========================================
          BATTLE ARENA
      ========================================== */}

      <div className="battle-arena">

        {/* Decorative stars */}

        <div className="arena-star star-one">
          ✦
        </div>

        <div className="arena-star star-two">
          ✧
        </div>

        <div className="arena-star star-three">
          ✦
        </div>

        <div className="arena-star star-four">
          •
        </div>


        {/* =====================================
            PLAYER
        ====================================== */}

        <div className="fighter player-fighter">

          <div className="fighter-info">

            <div className="fighter-name">
              YOU
            </div>

            <div className="hp-container">

              <div className="hp-text">
                <span>HP</span>

                <span>
                  {game.player_hp ?? 100}
                  /100
                </span>
              </div>

              <div className="hp-bar">

                <div
                  className="hp-fill player-hp"
                  style={{
                    width:
                      `${playerHp}%`,
                  }}
                />

              </div>

            </div>

          </div>


          <div className="player-platform" />

          <div className="player-character">
            🧙
          </div>

        </div>


        {/* =====================================
            VS
        ====================================== */}

        <div className="vs-text">
          VS
        </div>


        {/* =====================================
            ENEMY
        ====================================== */}

        <div
          className={`fighter enemy-fighter ${animation}`}
        >

          <div className="enemy-info">

            <div className="enemy-title-row">

              <div className="fighter-name">
                {enemy.name}
              </div>

              <div className="enemy-type">
                {enemy.type ||
                  "MYSTIC"}
              </div>

            </div>

            <div className="enemy-origin">
              Manifested from{" "}
              <strong>
                {enemy.source_object}
              </strong>
            </div>

            <div className="hp-container">

              <div className="hp-text">
                <span>HP</span>

                <span>
                  {currentEnemyHp}/
                  {enemyMaxHp}
                </span>
              </div>

              <div className="hp-bar">

                <div
                  className="hp-fill enemy-hp"
                  style={{
                    width:
                      `${enemyHpPercent}%`,
                  }}
                />

              </div>

            </div>

          </div>


          {/* Enemy aura */}

          <div className="enemy-aura" />

          <div className="enemy-energy energy-one">
            ✦
          </div>

          <div className="enemy-energy energy-two">
            ✧
          </div>

          <div className="enemy-energy energy-three">
            •
          </div>


          {/* Cartoon creature */}

          <div className="enemy-character">

            <div className="creature-shadow" />

            <div className="creature-body">

              {getCreatureEmoji(
                enemy.name
              )}

            </div>

          </div>

        </div>

      </div>


      {/* =========================================
          TRANSFORMATION OVERLAY
      ========================================== */}

      {animation === "transform" && (
        <div className="transformation-overlay">

          <div className="reality-ring ring-one" />
          <div className="reality-ring ring-two" />
          <div className="reality-ring ring-three" />

          <div className="transformation-content">

            <div className="transformation-small">
              REALITY DISTORTION
            </div>

            <div className="transformation-icon">
              ✦
            </div>

            <h1>
              REALITY SHIFT
            </h1>

            <p>
              {enemy.source_object}
              {" "}is becoming
            </p>

            <strong>
              {enemy.name}
            </strong>

          </div>

        </div>
      )}


      {/* =========================================
          BATTLE MESSAGE
      ========================================== */}

      <div className="battle-message">

        <span className="message-icon">
          ✦
        </span>

        <span>
          {message ||
            `A wild ${enemy.name} appeared!`}
        </span>

      </div>


      {/* =========================================
          BATTLE CONTROLS
      ========================================== */}

      <div className="battle-controls">

        <button
          className="battle-button attack-button"
          onClick={() =>
            handleAction("attack")
          }
          disabled={
            game.battle_over
          }
        >
          <span className="button-icon">
            ⚔
          </span>

          <span>
            ATTACK
          </span>
        </button>


        <button
          className="battle-button defend-button"
          onClick={() =>
            handleAction("defend")
          }
          disabled={
            game.battle_over
          }
        >
          <span className="button-icon">
            🛡
          </span>

          <span>
            DEFEND
          </span>
        </button>


        <button
          className="battle-button special-button"
          onClick={() =>
            handleAction("special")
          }
          disabled={
            game.battle_over
          }
        >
          <span className="button-icon">
            ✦
          </span>

          <span>
            SPECIAL
          </span>
        </button>


        <button
          className="battle-button scan-button"
          onClick={() =>
            handleAction("scan")
          }
          disabled={
            game.battle_over
          }
        >
          <span className="button-icon">
            🔎
          </span>

          <span>
            SCAN
          </span>
        </button>

      </div>


      {/* =========================================
          BATTLE STATUS
      ========================================== */}

      <div className="battle-footer">

        <span>
          TURN {game.turn || 1}
        </span>

        <span>
          •
        </span>

        <span>
          {game.battle_over
            ? "BATTLE COMPLETE"
            : "CHOOSE YOUR ACTION"}
        </span>

      </div>

    </div>
  );
}


/* =====================================================
   CREATURE VISUALS

   Temporary cartoon representations.

   Later these can be replaced by custom SVG creatures.
===================================================== */

function getCreatureEmoji(name) {

  const creatures = {

    Cybermite: "🤖",

    Bytefang: "🦇",

    Ironback: "🪨",

    Chairgeist: "👻",

    Thornling: "🌿",

    "Wind Talon": "🦅",

    "Screen Wraith": "👾",

    "Signal Phantom": "⚡",

    Gatekeeper: "🚪",

    Toxiblob: "🟢",

    "Reality Echo": "🔮",

  };

  return (
    creatures[name] ||
    "👾"
  );
}