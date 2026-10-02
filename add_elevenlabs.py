import sys

file_path = r"d:\massdrips-voice-agent\backend\voice\tts.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

elevenlabs_code = """
    @classmethod
    async def synthesize_with_elevenlabs(
        cls,
        text: str,
        voice_id: str,
    ) -> bytes:
        import os
        import httpx
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            logger.warning("ELEVENLABS_API_KEY not found in .env")
            return b""
            
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        data = {
            "text": text,
            "model_id": "eleven_turbo_v2_5",  # Fastest model for real-time
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=headers, timeout=10.0)
                if response.status_code == 200:
                    return response.content
                else:
                    logger.warning(f"ElevenLabs API Error: {response.status_code} - {response.text}")
                    return b""
        except Exception as e:
            logger.warning(f"ElevenLabs synthesis failed: {e}")
            return b""
"""

# Insert the code before synthesize_to_pcm_async if not already there
if "synthesize_with_elevenlabs" not in content:
    target = "    @classmethod\n    async def synthesize_to_pcm_async("
    content = content.replace(target, elevenlabs_code + "\n" + target)

# Modify synthesize_to_pcm_async to support elevenlabs provider
old_routing = """        if TTS_PROVIDER == "edge_tts":
            mp3_bytes = await cls.synthesize_with_edge_tts(clean, voice, speed)
            if mp3_bytes:
                # Convert MP3 to 16kHz PCM for WebSocket delivery
                return await loop.run_in_executor(None, _mp3_to_pcm16k, mp3_bytes)
            # Edge-TTS failed -- fall through to Kokoro
            logger.warning("Edge-TTS failed, falling back to Kokoro local TTS")"""

new_routing = """        if TTS_PROVIDER == "elevenlabs":
            import os
            voice_id = os.getenv("ELEVENLABS_VOICE_ID", voice)
            mp3_bytes = await cls.synthesize_with_elevenlabs(clean, voice_id)
            if mp3_bytes:
                return await loop.run_in_executor(None, _mp3_to_pcm16k, mp3_bytes)
            logger.warning("ElevenLabs failed, falling back to local TTS")
            
        if TTS_PROVIDER == "edge_tts":
            mp3_bytes = await cls.synthesize_with_edge_tts(clean, voice, speed)
            if mp3_bytes:
                return await loop.run_in_executor(None, _mp3_to_pcm16k, mp3_bytes)
            logger.warning("Edge-TTS failed, falling back to local TTS")"""

if 'TTS_PROVIDER == "elevenlabs":' not in content:
    content = content.replace(old_routing, new_routing)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("ElevenLabs integration added to tts.py")
