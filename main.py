# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, profile, chat, history, agent_stream, upload

app = FastAPI()

# Simplified CORS middleware - WORKING VERSION
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # allow only this origin (adjust if needed)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
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
    return {"status": "healthy", "jwt": "configured"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
