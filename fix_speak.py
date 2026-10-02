file_path = r"d:\massdrips-voice-agent\voxsales-app\src\components\LiveCallModal.tsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

old_speak = """  const speakAgentText = async (text: string) => {
    isProcessingRef.current = true;
    stopListening();
    try {
      const res = await fetch('http://localhost:8000/api/v1/smart/speak', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        
        return new Promise<void>((resolve) => {
          isAgentSpeakingRef.current = true;
          setIsAgentSpeaking(true);
          isProcessingRef.current = false;
          
          const audio = new Audio(url);
          audioPlayerRef.current = audio;
          
          audio.onended = () => {
            isAgentSpeakingRef.current = false;
            setIsAgentSpeaking(false);
            startListening();
            resolve();
          };
          audio.onerror = () => {
            isAgentSpeakingRef.current = false;
            setIsAgentSpeaking(false);
            startListening();
            resolve();
          };
          
          audio.play().catch(e => {
            console.error('Audio play error:', e);
            isAgentSpeakingRef.current = false;
            setIsAgentSpeaking(false);
            startListening();
            resolve();
          });
        });
      }
    } catch (e) {
      console.error(e);
    }
    isProcessingRef.current = false;
    startListening();
  };"""

new_speak = """  const speakAgentText = async (text: string) => {
    isProcessingRef.current = true;
    stopListening();
    try {
      const res = await fetch('http://localhost:8000/api/v1/smart/speak', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      if (res.ok) {
        const data = await res.json();
        if (data.audio_base64) {
          await playAudioBase64(data.audio_base64);
          return;
        }
      }
    } catch (e) {
      console.error(e);
    }
    isProcessingRef.current = false;
    startListening();
  };"""

content = content.replace(old_speak, new_speak)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed speakAgentText JSON bug!")
