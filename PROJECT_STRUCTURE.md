# Project Structure — Wellness AI Assistant

This document maps the full-stack architecture across both repositories so
anyone (including Antigravity) can see how the pieces fit together before
touching code. Two repos, one product: `agent-backend` (FastAPI API) and
`agent-Frontend` (React/Vite SPA).

---

## High-level architecture

```
┌─────────────────────┐        HTTPS / WSS        ┌──────────────────────┐
│   agent-Frontend     │ ─────────────────────────▶│    agent-backend      │
│   React + Vite SPA   │◀───────────────────────── │    FastAPI            │
└─────────────────────┘                            └──────────┬───────────┘
                                                                │
                                          ┌─────────────────────┼─────────────────────┐
                                          ▼                     ▼                     ▼
                                    MongoDB Atlas         Groq LLM API          Google OAuth
                                 (users, profiles,     (agent reasoning)      (social login)
                                  conversation turns)
```

**Flow of a chat message:**
`WellnessAssistantPage.jsx` → `api/chatApi.js` → `WS /ws/process-query` or
`POST /chat` → `orchestrator.py` → supervisor picks agents (`agents/*.py`) →
`output_synthesizer.py` builds the final answer → saved via `database.py` →
streamed/returned to the frontend.

---

## Backend — `agent-backend/`

```
agent-backend/
├── main.py                      # FastAPI app: CORS, router mounting, health check, entry point
├── config.py                    # Central env-var config (API keys, JWT secret, model name)
├── database.py                  # MongoDB access layer — users, profiles, conversation turns
├── requirements.txt             # Python dependencies
├── render.yaml                  # Render.com deployment config
├── .env                         # (gitignored) local secrets — GROQ_API_KEY, MONGODB_URI, etc.
│
├── models/                      # Pydantic request/response schemas
│   ├── user.py                  #   UserCreate, UserLogin, Token
│   ├── user_profile.py          #   UserProfile (legacy/simple shape)
│   ├── profileu.py              #   ProfileSetupRequest (current profile-setup schema)
│   └── message_history.py       #   MessageHistory (chat log shape)
│
├── utils/                       # Small, stateless helper modules
│   ├── jwt_handler.py           #   create/decode/verify JWTs
│   └── password_hash.py         #   hash/verify passwords (pbkdf2_sha256)
│
├── agents/                      # LLM "specialist" agents — the core AI logic
│   ├── groq_client.py           #   shared ChatGroq factory used by every agent
│   ├── intention_classifier.py  #   is this message wellness-related?
│   ├── supervisor_agent.py      #   decides which specialist agent runs next
│   ├── symptom_agent.py         #   analyzes reported symptoms
│   ├── diet_agent.py            #   nutrition suggestions
│   ├── fitness_agent.py         #   exercise/workout suggestions
│   ├── lifestyle_agent.py       #   sleep/stress/habit suggestions
│   └── output_synthesizer.py    #   merges all agent outputs into final Markdown report
│
├── orchestrator/
│   └── orchestrator.py          # Control loop: memory, intent, supervisor loop, synthesis, logging
│
└── routers/                     # FastAPI route groups (mounted in main.py)
    ├── auth.py                  #   POST /auth/signup, /auth/login
    ├── google_auth.py           #   GET /auth/google/login, /auth/google/callback
    ├── profile.py                #   POST /profile/setup, GET /profile/get
    ├── chat.py                  #   POST /chat (synchronous)
    ├── agent_stream.py          #   WS /ws/process-query (streaming)
    ├── history.py                #   GET/DELETE /history/{user_id}
    └── upload.py                 #   POST /upload/report (PDF medical report parsing)
```

### Backend conventions

| Concern | Convention |
|---|---|
| New endpoint | Add to the relevant file in `routers/`; if it's a new domain, create a new router + register it in `main.py` |
| New agent | Add to `agents/`, give it a `run_<name>_agent(...)` function, wire it into `orchestrator.py`'s supervisor loop |
| New DB entity | Add functions to `database.py` (keep the existing `save_*` / `get_*` naming pattern) |
| New request/response shape | Add a Pydantic model to `models/` rather than inline dicts |
| Config/secrets | Always go through `config.py` / `.env`, never hardcoded in a router or agent |

---

## Frontend — `agent-Frontend/`

```
agent-Frontend/
├── index.html                   # Vite HTML entry point
├── vite.config.js               # Vite build config
├── eslint.config.js             # Lint rules
├── package.json                 # Dependencies & scripts
│
├── public/                      # Static assets served as-is (PWA icons, etc.)
│
└── src/
    ├── main.jsx                 # React root — mounts <App /> to the DOM
    ├── App.jsx                  # Composes providers (Auth, Toaster) around the router
    ├── App.css / index.css      # Global styles
    │
    ├── theme/
    │   └── colors.js            # Design tokens (color palette) shared across components
    │
    ├── styles/
    │   └── global.css           # Global/shared CSS beyond App.css
    │
    ├── api/                     # All backend communication lives here — no component
    │   ├── client.js            #   shared Axios instance + auth header interceptor
    │   ├── auth.js               #   signup/login/google-auth calls
    │   ├── chatApi.js            #   chat + websocket message sending
    │   ├── historyApi.js         #   fetch/delete conversation history
    │   └── profileApi.js         #   profile get/setup calls
    │       # calls axios directly
    │
    ├── context/
    │   └── AuthContext.jsx      # Global auth state: user, token, login/logout actions
    │
    ├── hooks/
    │   └── useAuth.js           # Convenience hook wrapping AuthContext
    │
    ├── components/               # Reusable, page-agnostic UI pieces
    │   ├── AgentStream.jsx       #   live websocket agent-reasoning viewer
    │   ├── BmiCalculator.jsx     #   standalone BMI widget
    │   ├── Layout.jsx            #   shared page shell (nav + content area)
    │   ├── Navbar.jsx            #   top navigation bar
    │   ├── ProtectedRoute.jsx    #   route guard for authenticated-only pages
    │   └── Toaster.jsx           #   toast/notification renderer
    │
    ├── pages/                    # One file per route — composes components + api calls
    │   ├── LandingPage.jsx
    │   ├── LoginPage.jsx
    │   ├── SignupPage.jsx
    │   ├── GoogleCallBackPage.jsx
    │   ├── ProfileSetupPage.jsx
    │   ├── DashboardPage.jsx
    │   ├── WellnessAssistantPage.jsx
    │   ├── HistoryPage.jsx
    │   └── NotFoundPage.jsx
    │
    └── routes/
        └── AppRouter.jsx         # Route table — maps paths to pages, marks protected routes
```

### Frontend conventions

| Concern | Convention |
|---|---|
| New backend call | Add to the matching file in `api/` — components/pages never call `axios` directly |
| New route/page | Add a file to `pages/`, then register it in `routes/AppRouter.jsx` |
| New reusable UI | Add to `components/` only if used by 2+ pages; otherwise keep it local to the page |
| Auth-gated route | Wrap it with `<ProtectedRoute>` in `AppRouter.jsx` |
| Shared state | Goes in `context/`, consumed through a matching hook in `hooks/` |
| Styling | Prefer `theme/colors.js` tokens over hardcoded hex values |

---

## Where new files should go (quick decision guide)

- **"I'm adding a new AI capability"** → new file in `agents/` + wire into `orchestrator.py`
- **"I'm adding a new API endpoint"** → new/existing file in `routers/` + Pydantic model in `models/`
- **"I'm adding a new screen"** → new file in `src/pages/` + route in `AppRouter.jsx`
- **"I'm adding a new API call"** → new function in the matching `src/api/*.js` file
- **"I'm adding shared UI"** → `src/components/`
- **"I'm adding global state"** → `src/context/` + a hook in `src/hooks/`

This structure is already close to a clean, idiomatic layout for a FastAPI +
React project — the main opportunity is consistency (e.g. `models/user_profile.py`
vs `models/profileu.py` overlap) rather than restructuring.
