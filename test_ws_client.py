import asyncio
import websockets
import json

async def test_websocket():
    # Testing with fake tenant and lead IDs
    uri = "ws://localhost:8000/ws/voice/tenant_123/lead_456"
    
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected successfully!")
            
            # 1. Send JSON text
            test_msg = {"text": "Hello VoxSales from the test client!"}
            print(f"Sending JSON: {test_msg}")
            await websocket.send(json.dumps(test_msg))
            
            # Wait for response
            response = await websocket.recv()
            print(f"Received from server: {response}")
            
            # 2. Send Fake Binary Audio (4KB of zeros)
            fake_audio = b"\x00" * 4096 
            print(f"Sending {len(fake_audio)} bytes of binary audio data...")
            await websocket.send(fake_audio)
            
            print("Test completed successfully. Closing connection.")
            
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
