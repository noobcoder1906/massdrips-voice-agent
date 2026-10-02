import sys

file_path = r"d:\massdrips-voice-agent\backend\routes\smart.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Chunk 1
old1 = """@router.post("/speak")
async def live_speak_endpoint(req: SpeakRequest):
    \"\"\"Synthesizes text using ultra-realistic neural TTS engine and returns audio bytes.\"\"\"
    from fastapi.responses import Response
    from backend.voice.tts import KokoroTTS
    
    try:
        audio_bytes, media_type = await KokoroTTS.synthesize_neural_audio(
            text=req.text,
            voice=req.voice or "en-IN-PrabhatNeural",
            speed=req.speed or 1.05
        )
        return Response(content=audio_bytes, media_type=media_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS synthesis error: {e}")"""

new1 = """@router.post("/speak")
async def live_speak_endpoint(req: SpeakRequest):
    \"\"\"Synthesizes text using ultra-realistic neural TTS engine and returns audio bytes.\"\"\"
    from fastapi.responses import Response
    from backend.voice.tts import KokoroTTS
    import wave, io
    
    try:
        pcm_bytes = await KokoroTTS.synthesize_to_pcm_async(
            text=req.text,
            voice=req.voice or "en-IN-PrabhatNeural",
            speed=req.speed or 1.05
        )
        
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(pcm_bytes)
            
        return Response(content=buf.getvalue(), media_type="audio/wav")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS synthesis error: {e}")"""

# Chunk 2
old2 = """    # 3. Fast TTS synthesis -- routes to Edge-TTS or Kokoro based on TTS_PROVIDER env
    # Returns raw 16kHz 16-bit PCM bytes
    pcm_bytes = await KokoroTTS.synthesize_to_pcm_async(
        text=reply_text,
        voice=resolved_voice,
        speed=resolved_speed,
    )

    audio_base64 = ""
    media_type = "audio/pcm"
    if pcm_bytes:
        b64 = base64.b64encode(pcm_bytes).decode("utf-8")
        audio_base64 = f"data:{media_type};base64,{b64}"""

new2 = """    # 3. Fast TTS synthesis
    pcm_bytes = await KokoroTTS.synthesize_to_pcm_async(
        text=reply_text,
        voice=resolved_voice,
        speed=resolved_speed,
    )

    audio_base64 = ""
    media_type = "audio/wav"
    if pcm_bytes:
        import wave, io
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(pcm_bytes)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        audio_base64 = f"data:{media_type};base64,{b64}"""

if old1 in content:
    content = content.replace(old1, new1)
else:
    print("WARNING: Chunk 1 not found!")

if old2 in content:
    content = content.replace(old2, new2)
else:
    print("WARNING: Chunk 2 not found!")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("smart.py updated successfully.")
