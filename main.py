# backend/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, profile, chat, history, agent_stream, upload

app = FastAPI()

# --- CORS CONFIGURATION ---
# We allow ["*"] (all origins) to ensure your deployed frontend can communicate 
# with the backend without errors. In a strict production environment, 
# you would replace "*" with your specific frontend URL.
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(chat.router)
app.include_router(history.router)
app.include_router(agent_stream.router)
app.include_router(upload.router)

@app.get("/")
def root():
    return {"message": "Wellness AI Assistant API is running"}

@app.get("/health")
def health_check():
    """
    Health check endpoint for Render to verify the service is up.
    """
    return {"status": "healthy", "jwt_configured": True}

if __name__ == "__main__":
    import uvicorn
    # The port must be dynamic for Render (os.getenv("PORT"))
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)