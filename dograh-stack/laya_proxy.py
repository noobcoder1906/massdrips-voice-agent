"""
Dograh -> Laya Proxy Server
This sits between Dograh and LM Studio. Dograh sends an OpenAI chat request to this proxy.
This proxy runs the Laya intent router. If it's a fast-bypass (e.g. DNC, price query), it returns the response instantly.
Otherwise, it forwards the request to the real LM Studio server.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
import uvicorn
import json
import time
import sys
import os

app = FastAPI(title="Laya Dograh Proxy")

# Import the existing Laya engine from the custom backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from agent.laya_router import laya_engine

LM_STUDIO_URL = "http://host.docker.internal:1234/v1/chat/completions"

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
    
    # Extract the last user message
    user_msg = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_msg = msg.get("content", "")
            break

    # 1. Laya Fast Routing
    if user_msg:
        decision = laya_engine.classify_intent(user_msg)
        if decision["bypass_llm"]:
            print(f"[LAYA PROXY] Intercepted! Intent: {decision['intent']}")
            # Mock an OpenAI response
            response_data = {
                "id": "chatcmpl-laya",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": body.get("model", "laya-fast"),
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": decision["fast_reply"]
                    },
                    "finish_reason": "stop"
                }]
            }
            return JSONResponse(content=response_data)
        
        # Inject Laya context into the system prompt if not bypassed
        if messages and messages[0].get("role") == "system":
            messages[0]["content"] += f"\n[LAYA CONTEXT]: Intent detected: {decision['intent']}. Use this context."

    # 2. Forward to LM Studio
    print("[LAYA PROXY] Forwarding to LM Studio...")
    async with httpx.AsyncClient() as client:
        req = client.build_request("POST", LM_STUDIO_URL, json=body, timeout=60.0)
        r = await client.send(req, stream=body.get("stream", False))
        
        if body.get("stream", False):
            async def generate():
                async for chunk in r.aiter_raw():
                    yield chunk
            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            return JSONResponse(content=r.json(), status_code=r.status_code)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=1235)
