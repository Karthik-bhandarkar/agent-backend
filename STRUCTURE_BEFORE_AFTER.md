# Project Structure Enhancement — Before & After (Backend + Frontend)

One reference file covering both `agent-backend` and `agent-Frontend`: current
structure, proposed structure, why each change matters, and the exact
prompts to run in Antigravity — in order — to execute the migration safely.

⚠️ **This restructures real files and imports, unlike the commenting pass.**
Work on a separate git branch, run one prompt at a time, and test the app
after each one before moving to the next. Don't run this in the same
session as the commenting work.

---

## PART 1 — Backend (`agent-backend`)

### BEFORE (current)

```
agent-backend/
├── main.py
├── config.py                  # JWT_SECRET hardcoded in source
├── database.py                # one 250-line file: users + profiles + conversations
├── requirements.txt
├── render.yaml
│
├── models/
│   ├── user.py
│   ├── user_profile.py        # overlaps with profileu.py below
│   ├── profileu.py            # overlaps with user_profile.py above
│   └── message_history.py
│
├── utils/
│   ├── jwt_handler.py
│   └── password_hash.py
│
├── agents/                    # already well organized
│   ├── groq_client.py
│   ├── intention_classifier.py
│   ├── supervisor_agent.py
│   ├── symptom_agent.py
│   ├── diet_agent.py
│   ├── fitness_agent.py
│   ├── lifestyle_agent.py
│   └── output_synthesizer.py
│
├── orchestrator/
│   └── orchestrator.py        # uses print() for debug logging
│
└── routers/
    ├── auth.py
    ├── google_auth.py         # uses print() for debug logging
    ├── profile.py              # trusts a raw ?user_id= query param — no auth check
    ├── chat.py
    ├── agent_stream.py
    ├── history.py
    └── upload.py
```

### AFTER (proposed)

```
agent-backend/
├── main.py
├── config.py                  # UPDATED: JWT_SECRET now read from env
├── requirements.txt
├── render.yaml
├── .env.example                # NEW: documents required env vars, no real secrets
│
├── core/                       # NEW: cross-cutting concerns
│   ├── security.py               # merged jwt_handler.py + password_hash.py
│   ├── deps.py                    # NEW: get_current_user() FastAPI dependency
│   └── logging_config.py          # NEW: replaces print() with real logging
│
├── db/                         # REPLACES database.py — split by entity
│   ├── client.py                  # Mongo connection setup only
│   ├── users_repo.py
│   ├── profiles_repo.py
│   └── conversations_repo.py
│
├── schemas/                    # RENAMED from models/ — duplicates merged
│   ├── auth_schemas.py            # UserCreate, UserLogin, Token
│   ├── profile_schemas.py         # merged user_profile.py + profileu.py
│   └── chat_schemas.py            # ChatRequest, MessageHistory
│
├── agents/                     # unchanged
├── orchestrator/                # unchanged internally, logging swapped for print()
│
├── routers/                    # same filenames, internals updated
│   ├── auth.py
│   ├── google_auth.py
│   ├── profile.py                 # UPDATED: user identified via JWT, not query param
│   ├── chat.py
│   ├── agent_stream.py
│   ├── history.py
│   └── upload.py
│
└── tests/                      # NEW
    ├── conftest.py
    ├── test_auth.py
    └── test_profile.py
```

### Why (backend)

| Change | Problem it fixes |
|---|---|
| `core/security.py` | Merges two files that are always used together (`jwt_handler.py`, `password_hash.py`) |
| `core/deps.py` → `get_current_user` | **Security fix**: today anyone can call `/profile/get?user_id=<anyone>` — a JWT-derived dependency closes this |
| `db/` split by entity | `database.py` mixes users, profiles, and conversations in one file — hard to test or extend safely |
| `schemas/` replaces `models/` | Removes the current duplication between `user_profile.py` and `profileu.py` |
| `config.py` reads `JWT_SECRET` from env | The signing secret is currently hardcoded and committed to git |
| `.env.example` | New contributors have to reverse-engineer required env vars today |
| `core/logging_config.py` | `print()` debugging doesn't integrate with production log tooling |
| `tests/` | No automated tests exist today — regressions go unnoticed |

---

## PART 2 — Frontend (`agent-Frontend`)

### BEFORE (current)

```
agent-Frontend/
├── index.html
├── vite.config.js
├── package.json
│
├── public/
│
└── src/
    ├── main.jsx
    ├── App.jsx
    ├── App.css / index.css
    │
    ├── theme/
    │   └── colors.js
    ├── styles/
    │   └── global.css
    ├── assets/
    │   └── react.svg           # unused Vite boilerplate
    │
    ├── api/
    │   ├── client.js
    │   ├── auth.js
    │   ├── chatApi.js
    │   ├── historyApi.js
    │   └── profileApi.js
    │
    ├── context/
    │   └── AuthContext.jsx
    ├── hooks/
    │   └── useAuth.js
    │
    ├── components/
    │   ├── AgentStream.jsx
    │   ├── BmiCalculator.jsx    # BMI math + route strings likely inlined
    │   ├── Layout.jsx
    │   ├── Navbar.jsx           # nav links likely hardcode path strings
    │   ├── ProtectedRoute.jsx
    │   └── Toaster.jsx
    │
    ├── pages/                    # 9 page files — likely hardcode route strings too
    │
    └── routes/
        └── AppRouter.jsx          # single source of truth for real paths
```

### AFTER (proposed)

```
agent-Frontend/
├── index.html
├── vite.config.js
├── package.json
├── .env.example                 # NEW
│
├── public/
│
└── src/
    ├── main.jsx
    ├── App.jsx
    ├── App.css / index.css
    │
    ├── constants/                 # NEW
    │   ├── routes.js                 # ROUTES.LOGIN, ROUTES.DASHBOARD, etc.
    │   └── config.js                 # API base URL and other constants
    │
    ├── utils/                     # NEW
    │   └── formatters.js             # shared helpers (BMI rounding, dates, etc.)
    │
    ├── theme/
    │   └── colors.js
    ├── styles/
    │   └── global.css
    │                                 # assets/react.svg REMOVED (unused)
    │
    ├── api/                        # unchanged — already clean
    ├── context/                     # unchanged
    ├── hooks/                       # unchanged
    ├── components/                  # unchanged files, internals use ROUTES constants
    ├── pages/                       # unchanged files, internals use ROUTES constants
    └── routes/
        └── AppRouter.jsx             # now imports from constants/routes.js
```

### Why (frontend)

| Change | Problem it fixes |
|---|---|
| `constants/routes.js` | Route strings are likely duplicated across pages/components — one typo silently breaks a link |
| `constants/config.js` | Centralizes the API base URL instead of repeating `import.meta.env.VITE_API_URL` |
| `utils/formatters.js` | Gives shared logic (like BMI rounding) one home instead of being copy-pasted if reused |
| Remove `assets/react.svg` | Dead file, no functional purpose |

---

