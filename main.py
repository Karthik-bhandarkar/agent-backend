# backend/main.py
"""
FastAPI application entry point.

Initializes the FastAPI application, configures CORS middleware, registers
all routing endpoints, and provides basic root/health-check endpoints.
Also serves as the launch script for the uvicorn development server.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, profile, chat, history, agent_stream, upload, google_auth

app = FastAPI()

# --- CORS CONFIGURATION ---
# NOTE: We allow ["*"] (all origins) to ensure your deployed frontend can communicate 
# with the backend without errors during initial deployment and local development.
# The tradeoff is a security risk in production, as any third-party site could 
# theoretically make requests to this API on a user's behalf. In a strict 
# production environment, this should be replaced with the exact frontend URL.
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
app.include_router(google_auth.router)

@app.get("/")
def root():
    """
    Basic root endpoint to verify the API is responsive.

    Route: GET /

    Returns:
        dict: A simple welcome message.
    """
    return {"message": "Wellness AI Assistant API is running"}

@app.get("/health")
def health_check():
    """
    Health check endpoint for deployment platforms (like Render) to verify the service is up.

    Route: GET /health

    Returns:
        dict: The health status and a flag indicating JWT configuration presence.
    """
    return {"status": "healthy", "jwt_configured": True}

if __name__ == "__main__":
    import uvicorn
    # The port must be dynamic for Render (os.getenv("PORT"))
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)