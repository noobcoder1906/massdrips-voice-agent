from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio

router = APIRouter()

@router.websocket("/ws/voice/{tenant_id}/{lead_id}")
async def voice_websocket_endpoint(websocket: WebSocket, tenant_id: str, lead_id: str):
    """
    WebSocket endpoint for handling real-time audio streams.
    Receives raw PCM audio chunks from the client/Twilio and sends back TTS audio.
    """
    await websocket.accept()
    print(f"[WebSocket] Call connected! Tenant: {tenant_id} | Lead: {lead_id}")
    
    try:
        while True:
            # Wait for data from the client
            data = await websocket.receive()
            
            if "bytes" in data:
                audio_chunk = data["bytes"]
                print(f"[WebSocket] Received audio chunk: {len(audio_chunk)} bytes")
                # TODO in Phase 2: Feed 'audio_chunk' into Silero VAD buffer here
                
            elif "text" in data:
                text_msg = data["text"]
                print(f"[WebSocket] Received JSON/Text: {text_msg}")
                # We can respond back immediately over the socket
                await websocket.send_text(f"Server acknowledged: {text_msg}")
                
    except WebSocketDisconnect:
        print(f"[WebSocket] Call disconnected. Tenant: {tenant_id} | Lead: {lead_id}")
    except Exception as e:
        print(f"[WebSocket] Error occurred: {str(e)}")
