import { useState } from "react";

import {
  signIn,
  signUp
} from "./auth.js";


export default function Auth({
  onLogin
}) {

  const [mode, setMode] =
    useState("login");

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [username, setUsername] =
    useState("");

  const [fullName, setFullName] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [message, setMessage] =
    useState("");


  // =========================================================
  // SWITCH LOGIN / SIGNUP
  // =========================================================

  function switchMode(newMode) {

    setMode(newMode);

    setError("");

    setMessage("");

  }


  // =========================================================
  // SUBMIT
  // =========================================================

  async function handleSubmit(event) {

    event.preventDefault();

    setError("");

    setMessage("");

    setLoading(true);


    try {

      // =====================================================
      // SIGN UP
      // =====================================================

      if (mode === "signup") {

        if (!username.trim()) {

          throw new Error(
            "Please enter a username."
          );

        }


        if (password.length < 6) {

          throw new Error(
            "Password must contain at least 6 characters."
          );

        }


        const data = await signUp({

          email: email.trim(),

          password,

          username: username.trim(),

          fullName: fullName.trim()

        });


        // ---------------------------------------------------
        // EMAIL VERIFICATION REQUIRED
        // ---------------------------------------------------

        if (!data.session) {

          setMessage(
            "Account created successfully. Please check your email and verify your account before logging in."
          );

          setMode("login");

          setPassword("");

          return;

        }


        // ---------------------------------------------------
        // DIRECT LOGIN
        // ---------------------------------------------------

        if (data.user) {

          onLogin(data.user);

        }

      }


      // =====================================================
      // LOGIN
      // =====================================================

      else {

        const data = await signIn({

          email: email.trim(),

          password

        });


        if (!data.user) {

          throw new Error(
            "Login failed."
          );

        }


        onLogin(data.user);

      }

    }

    catch (err) {

      console.error(
        "Authentication error:",
        err
      );


      let errorMessage =
        err?.message ||
        "Something went wrong.";


      // Friendlier Supabase messages

      if (
        errorMessage
          .toLowerCase()
          .includes("invalid login credentials")
      ) {

        errorMessage =
          "Incorrect email or password.";

      }


      if (
        errorMessage
          .toLowerCase()
          .includes("user already registered")
      ) {

        errorMessage =
          "An account with this email already exists.";

      }


      if (
        errorMessage
          .toLowerCase()
          .includes("email not confirmed")
      ) {

        errorMessage =
          "Please verify your email before logging in.";

      }


      setError(errorMessage);

    }

    finally {

      setLoading(false);

    }

  }


  // =========================================================
  // UI
  // =========================================================

  return (

    <div className="auth-page">

      <div className="auth-background-grid" />

      <div className="auth-glow auth-glow-one" />

      <div className="auth-glow auth-glow-two" />


      <div className="auth-card">


        {/* =================================================
            LOGO
            ================================================= */}

        <div className="auth-brand">

          <div className="auth-logo">

            REALITY<span>:UNSEEN</span>

          </div>

          <div className="auth-tagline">

            AI-GENERATED REALITY

          </div>

        </div>


        {/* =================================================
            TITLE
            ================================================= */}

        <div className="auth-heading">

          <h1>

            {mode === "login"
              ? "ENTER REALITY"
              : "CREATE YOUR REALITY"
            }

          </h1>


          <p>

            {mode === "login"
              ? "Continue your story."
              : "Create an account and begin your story."
            }

          </p>

        </div>


        {/* =================================================
            LOGIN / SIGNUP TABS
            ================================================= */}

        <div className="auth-tabs">

          <button
            type="button"
            className={
              mode === "login"
                ? "auth-tab active"
                : "auth-tab"
            }
            onClick={() =>
              switchMode("login")
            }
          >

            LOGIN

          </button>


          <button
            type="button"
            className={
              mode === "signup"
                ? "auth-tab active"
                : "auth-tab"
            }
            onClick={() =>
              switchMode("signup")
            }
          >

            SIGN UP

          </button>

        </div>


        {/* =================================================
            FORM
            ================================================= */}

        <form
          className="auth-form"
          onSubmit={handleSubmit}
        >


          {/* =================================================
              SIGNUP ONLY
              ================================================= */}

          {mode === "signup" && (

            <>

              <div className="auth-field">

                <label>
                  USERNAME
                </label>

                <input
                  type="text"
                  placeholder="Enter username"
                  value={username}
                  onChange={(event) =>
                    setUsername(
                      event.target.value
                    )
                  }
                  autoComplete="username"
                  required
                />

              </div>


              <div className="auth-field">

                <label>
                  FULL NAME
                </label>

                <input
                  type="text"
                  placeholder="Enter your name"
                  value={fullName}
                  onChange={(event) =>
                    setFullName(
                      event.target.value
                    )
                  }
                  autoComplete="name"
                />

              </div>

            </>

          )}


          {/* =================================================
              EMAIL
              ================================================= */}

          <div className="auth-field">

            <label>
              EMAIL
            </label>

            <input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(event) =>
                setEmail(
                  event.target.value
                )
              }
              autoComplete="email"
              required
            />

          </div>


          {/* =================================================
              PASSWORD
              ================================================= */}

          <div className="auth-field">

            <label>
              PASSWORD
            </label>

            <input
              type="password"
              placeholder="Enter password"
              value={password}
              onChange={(event) =>
                setPassword(
                  event.target.value
                )
              }
              autoComplete={
                mode === "login"
                  ? "current-password"
                  : "new-password"
              }
              minLength={6}
              required
            />

          </div>


          {/* =================================================
              ERROR
              ================================================= */}

          {error && (

            <div className="auth-alert error">

              <span>
                !
              </span>

              {error}

            </div>

          )}


          {/* =================================================
              SUCCESS MESSAGE
              ================================================= */}

          {message && (

            <div className="auth-alert success">

              <span>
                ✓
              </span>

              {message}

            </div>

          )}


          {/* =================================================
              SUBMIT
              ================================================= */}

          <button
            type="submit"
            className="auth-submit"
            disabled={loading}
          >

            {loading

              ? "CONNECTING..."

              : mode === "login"

                ? "ENTER REALITY"

                : "CREATE ACCOUNT"

            }


            {!loading && (

              <span className="auth-arrow">

                →

              </span>

            )}

          </button>


        </form>


        {/* =================================================
            FOOTER
            ================================================= */}

        <div className="auth-footer">

          {mode === "login"

            ? "Don't have an account?"

            : "Already have an account?"

          }


          <button
            type="button"
            onClick={() =>
              switchMode(
                mode === "login"
                  ? "signup"
                  : "login"
              )
            }
          >

            {mode === "login"

              ? "CREATE ACCOUNT"

              : "LOGIN"

            }

          </button>

        </div>


        {/* =================================================
            STATUS
            ================================================= */}

        <div className="auth-status">

          <span className="status-dot" />

          SECURE SUPABASE AUTHENTICATION

        </div>


      </div>

    </div>

  );

}