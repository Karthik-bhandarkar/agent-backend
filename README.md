# Digital Wellness Assistant

A full-stack application for digital wellness, featuring a React frontend and a FastAPI backend.

## Structure
- `frontend/`: React application (Vite)
- `backend/`: FastAPI application

## Local Setup

### Backend
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables in a `.env` file (see `config.py` for required variables).
4. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```

## Deployment on Render

This project includes a `render.yaml` configuration for easy deployment on Render.

### Prerequisites
- A [Render](https://render.com) account.
- A GitHub account connected to Render.
- The project pushed to a GitHub repository.

### Steps

1. **Move Configuration File**:
   Ensure `render.yaml` is in the **root** of your repository (not inside `backend/`).
   - If it is currently in `backend/`, move it to the root project folder: `d:\Digital-Wellness-Assistant\render.yaml`.

2. **Create Blueprint**:
   - Go to your [Render Dashboard](https://dashboard.render.com).
   - Click **New +** and select **Blueprint**.
   - Connect your GitHub repository.
   - Render will automatically detect the `render.yaml` file.

3. **Configure Environment Variables**:
   During the setup (or after in the "Environment" tab), add the following secrets:
   - `GROQ_API_KEY`: Your Groq API Key.
   - `GOOGLE_CLIENT_ID`: Your Google Client ID.
   - `GOOGLE_CLIENT_SECRET`: Your Google Client Secret.
   - `JWT_SECRET`: (Optional) Override the default secret if needed.

4. **Deploy**:
   - Click **Apply** or **Create Blueprint**.
   - Render will build and deploy your backend service.

5. **Verify**:
   - Once deployed, your service will have a public URL (e.g., `https://digital-wellness-backend.onrender.com`).
   - Visit `/health` endpoint to verify it is running.
