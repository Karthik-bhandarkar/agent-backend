# backend/routers/agent_stream.py
from fastapi import APIRouter, WebSocket
import asyncio
from typing import List, Dict, Any

router = APIRouter()

from orchestrator.orchestrator import process_query_generator

@router.websocket("/ws/process-query")
async def process_query_ws(websocket: WebSocket):
    await websocket.accept()
    print("WS Connected")
    try:
        init = await websocket.receive_json()
        print(f"WS Received init: {init}")
        query = init.get("query", "")

        user_id = init.get("user_id")
        if not user_id:
             await websocket.send_json({"type": "error", "text": "user_id is required"})
             return

        # Iterate over real orchestrator events
        for event in process_query_generator(user_id, query):
            if event["type"] == "log":
                # Send "agent" type message to frontend
                await websocket.send_json({
                    "type": "agent",
                    "agent": event["agent"],
                    "text": event["message"]
                })
                # tiny sleep to ensure frontend has time to render if it's too fast
                await asyncio.sleep(0.1)
            
            elif event["type"] == "final":
                # Send final answer
                await websocket.send_json({
                    "type": "final",
                    "answer": event["response"],
                    "agents_used": event["agents_used"],
                    "reasoning_logs": event.get("reasoning_logs", [])
                })

    except Exception as e:
        print(f"CRITICAL WS ERROR: {e}")
        import traceback
        traceback.print_exc()
        await websocket.send_json({"type": "error", "text": f"WebSocket error: {str(e)}"})
    finally:
        await websocket.close()
