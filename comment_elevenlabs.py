file_path = r"d:\massdrips-voice-agent\backend\voice\tts.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Comment out elevenlabs routing
old_routing = """        if TTS_PROVIDER == "elevenlabs":
            import os
            voice_id = os.getenv("ELEVENLABS_VOICE_ID", voice)
            mp3_bytes = await cls.synthesize_with_elevenlabs(clean, voice_id)
            if mp3_bytes:
                return await loop.run_in_executor(None, _mp3_to_pcm16k, mp3_bytes)
            logger.warning("ElevenLabs failed, falling back to local TTS")"""

new_routing = """        # if TTS_PROVIDER == "elevenlabs":
        #     import os
        #     voice_id = os.getenv("ELEVENLABS_VOICE_ID", voice)
        #     mp3_bytes = await cls.synthesize_with_elevenlabs(clean, voice_id)
        #     if mp3_bytes:
        #         return await loop.run_in_executor(None, _mp3_to_pcm16k, mp3_bytes)
        #     logger.warning("ElevenLabs failed, falling back to local TTS")"""

content = content.replace(old_routing, new_routing)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("ElevenLabs commented out.")
