# Code Commenting Standard

This document defines how comments should look across **agent-backend** (FastAPI /
Python) and **agent-Frontend** (React / Vite / JSX). Give this file to Antigravity
alongside the prompts in `ANTIGRAVITY_PROMPTS.md` so every file ends up consistent.

## Core rules

1. **File header at the top of every file.** 3–6 lines: what the file does, where it
   fits in the app, and what it exports.
2. **Docstring/JSDoc on every function, class, and route handler.** Purpose,
   parameters, return value, side effects (DB writes, external API calls, etc.).
3. **Inline comments explain *why*, not *what*.** Skip comments that just restate
   the line (`# increment counter` above `count += 1`). Add them for non-obvious
   logic: business rules, workarounds, edge cases, magic numbers.
4. **No logic changes.** Comments are additive only — never reformat, rename, or
   "fix" code while commenting it. If something looks buggy, leave a `# NOTE:` or
   `# TODO:` flagging it instead of changing it.
5. **Consistent voice.** Present tense, third person ("Loads the user profile"),
   not "This will load..." or "I load...".
6. **Don't over-comment.** A getter that returns `self.name` doesn't need a
   docstring essay. Match comment density to actual complexity.

---

## Python (FastAPI backend)

### File header

```python
# backend/routers/auth.py
"""
Authentication routes: signup and login.

Issues JWTs on successful signup/login and stores hashed passwords via
utils/password_hash.py. Mounted in main.py under the "/auth" prefix.
"""
```

### Function / route docstrings (Google style)

```python
@router.post("/login")
def login(req: LoginRequest):
    """
    Authenticate a user by email + password and return a JWT.

    Args:
        req: Parsed request body containing `email` and `password`.

    Returns:
        dict: id, email, name, profile_complete flag, and signed JWT token.

    Raises:
        HTTPException(401): if the email doesn't exist or the password
            doesn't match the stored hash.
    """
    user = get_user_by_email(req.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    ...
```

### Inline comments — only where logic isn't obvious

```python
# Default new users to an incomplete profile so the frontend can redirect
# them to /profile-setup before showing the dashboard.
user_data["profile_complete"] = False

# Use a short server-selection timeout so the API starts up fast even if
# MongoDB is unreachable, instead of hanging on boot.
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
```

### Pydantic models — comment non-obvious fields only

```python
class Token(BaseModel):
    """Response shape returned by /auth/signup and /auth/login."""
    access_token: str
    token_type: str
    user_id: int
    profile_complete: bool  # drives frontend redirect to profile setup
    message: Optional[str] = None
```

### Full before/after — `agents/groq_client.py`

**Before:**
```python
from langchain_groq import ChatGroq
from config import GROQ_API_KEY, MODEL_NAME

def get_llm():
    return ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model=MODEL_NAME,
        temperature=0.2,
        max_tokens=512
    )
```

**After:**
```python
# backend/agents/groq_client.py
"""
Shared factory for the Groq-hosted LLM client.

Every agent (diet, fitness, symptom, lifestyle, supervisor, etc.) calls
get_llm() to obtain the same configured model instance instead of
constructing ChatGroq directly, keeping model settings in one place.
"""

from langchain_groq import ChatGroq
from config import GROQ_API_KEY, MODEL_NAME


def get_llm():
    """
    Build a ChatGroq client using the app's configured API key and model.

    Returns:
        ChatGroq: configured with low temperature (0.2) for consistent,
        less "creative" wellness advice, and a 512-token cap to keep
        responses short across all agents.
    """
    return ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model=MODEL_NAME,
        temperature=0.2,
        max_tokens=512
    )
```

---

## JavaScript / React (frontend)

### File header

```javascript
/**
 * src/api/chatApi.js
 *
 * API calls for the chat/agent-stream feature. Wraps the shared Axios
 * client (see api/client.js) so components never call axios directly.
 */
```

### Function-level JSDoc

```javascript
/**
 * Send a user message to the backend and get the assistant's reply.
 *
 * @param {string} userId - Mongo ObjectId string of the logged-in user.
 * @param {string} message - Raw text typed by the user.
 * @returns {Promise<{response: string, agents_used: string[]}>}
 *   The assistant's reply plus which agents contributed to it.
 * @throws Will throw if the request fails (network error or non-2xx status);
 *   callers should wrap this in try/catch and show a toast on failure.
 */
export async function sendChatMessage(userId, message) {
  const { data } = await client.post("/chat", { user_id: userId, message });
  return data;
}
```

### React components — header + prop docs, not line-by-line noise

```jsx
/**
 * BmiCalculator.jsx
 *
 * Standalone BMI widget used on the dashboard. Takes height/weight either
 * from props (if the profile already has them) or lets the user type
 * their own values to get an instant estimate — this does NOT write back
 * to the user's saved profile.
 */

/**
 * @param {Object} props
 * @param {number} [props.heightCm] - Pre-filled height from the user's profile.
 * @param {number} [props.weightKg] - Pre-filled weight from the user's profile.
 */
export default function BmiCalculator({ heightCm, weightKg }) {
  // Local, editable copies — kept separate from the profile so this widget
  // can be used for "what if" calculations without mutating saved data.
  const [height, setHeight] = useState(heightCm ?? "");
  const [weight, setWeight] = useState(weightKg ?? "");

  const bmi = useMemo(() => {
    if (!height || !weight) return null;
    const meters = height / 100;
    return +(weight / (meters * meters)).toFixed(2); // round to 2 decimals
  }, [height, weight]);

  return (/* ... */);
}
```

### Hooks

```javascript
/**
 * useAuth.js
 *
 * Convenience hook exposing the current user, login/logout actions, and
 * loading state from AuthContext. Components should use this instead of
 * importing AuthContext directly.
 */
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    // Fails loudly if a component forgets to wrap the tree in <AuthProvider>.
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
```

---

## Quick checklist (paste into PR description or review)

- [ ] Every file has a header comment (purpose + role in the app)
- [ ] Every function/class/route/component has a docstring or JSDoc block
- [ ] Non-obvious logic has an inline comment explaining *why*
- [ ] No trivial/obvious comments cluttering simple lines
- [ ] No code logic was changed, only comments added
- [ ] Naming/voice is consistent with this document
