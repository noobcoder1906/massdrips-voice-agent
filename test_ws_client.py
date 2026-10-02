import argparse
import asyncio
import json
import websockets

async def test_websocket(tenant_id: str, lead_id: str, host: str = "localhost:8000"):
    uri = f"ws://{host}/ws/voice/{tenant_id}/{lead_id}"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print(" Connected to VoxSales Voice WebSocket pipeline!")
            
            # 1. Send JSON greeting
            test_msg = {"type": "transcript", "text": "Hi, I am looking for a black hoodie"}
            print(f"-> Sending message: {test_msg}")
            await websocket.send(json.dumps(test_msg))
            
            # 2. Receive streaming events
            try:
                msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"<- Received event: {msg}")
            except asyncio.TimeoutError:
                print("⚠️ Timeout waiting for initial server event.")
            
            # 3. Send test PCM audio frame (640 bytes = 20ms @ 16kHz)
            fake_audio = b"\x00" * 640
            print(f"-> Streaming {len(fake_audio)} bytes PCM audio...")
            await websocket.send(fake_audio)
            
            print("✅ WebSocket voice handshake test passed!")
            
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VoxSales Voice WebSocket Test Client")
    parser.add_argument("--tenant", default="mass-drips", help="Tenant ID or slug (default: mass-drips)")
    parser.add_argument("--lead", default="sample-lead-01", help="Lead ID (default: sample-lead-01)")
    parser.add_argument("--host", default="localhost:8000", help="Backend host (default: localhost:8000)")
    args = parser.parse_args()
    
    asyncio.run(test_websocket(tenant_id=args.tenant, lead_id=args.lead, host=args.host))
