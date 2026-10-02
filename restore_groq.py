import os

file_path = r"d:\massdrips-voice-agent\voxsales-app\src\components\LiveCallModal.tsx"

react_code = """import React, { useState, useEffect, useRef } from 'react';
import { X, Mic, Volume2, PhoneOff, ArrowRight, Sparkles, MessageSquare, PhoneCall } from 'lucide-react';
import Button from './Button';

interface LiveCallModalProps {
  isOpen?: boolean;
  onClose: () => void;
  onCallCompleted?: () => void;
  leadName?: string;
  leadPhone?: string;
  brandName?: string;
}

export default function LiveCallModal({ isOpen, onClose, leadName = 'Customer', brandName = 'MASS DRIPS' }: LiveCallModalProps) {
  if (!isOpen) return null;

  const [callState, setCallState] = useState<'idle' | 'connecting' | 'connected' | 'ended'>('idle');
  const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState<{ role: 'user' | 'agent', text: string, ts: string }[]>([]);
  const [callDuration, setCallDuration] = useState(0);
  
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<BlobPart[]>([]);
  
  const isAgentSpeakingRef = useRef(false);
  const isProcessingRef = useRef(false);
  
  // VAD (Silence Detection) Refs
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const silenceTimerRef = useRef<any>(null);
  const isSpeakingRef = useRef(false);

  const addTranscript = (role: 'user' | 'agent', text: string) => {
    const ts = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setTranscript(prev => [...prev, { role, text, ts }]);
  };

  useEffect(() => {
    let interval: any;
    if (callState === 'connected') {
      interval = setInterval(() => setCallDuration(p => p + 1), 1000);
      startConversation();
    }
    return () => clearInterval(interval);
  }, [callState]);

  const startConversation = async () => {
    const greeting = "Hey there! Aria this side from MASS DRIPS. We are running an exclusive drop right now. What are you looking for today, hoodies or oversized tees?";
    addTranscript('agent', greeting);
    await speakAgentText(greeting);
  };

  const startListening = async () => {
    if (callState !== 'connected' || isProcessingRef.current || isAgentSpeakingRef.current) return;
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await processUserAudio(audioBlob);
        
        // Cleanup tracks
        stream.getTracks().forEach(track => track.stop());
      };

      // Set up VAD (Silence Detection)
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      audioContextRef.current = audioContext;
      const analyser = audioContext.createAnalyser();
      analyser.minDecibels = -60; // Sensitivity
      analyserRef.current = analyser;
      
      const source = audioContext.createMediaStreamSource(stream);
      source.connect(analyser);
      
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      
      const checkAudioLevel = () => {
        if (!isListening || isProcessingRef.current) return;
        
        analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
        const average = sum / dataArray.length;
        
        // If volume is above threshold, user is speaking
        if (average > 15) {
          isSpeakingRef.current = true;
          if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
        } else if (isSpeakingRef.current) {
          // Volume dropped below threshold, start 1.5s silence countdown
          if (!silenceTimerRef.current) {
            silenceTimerRef.current = setTimeout(() => {
              isSpeakingRef.current = false;
              stopListeningAndProcess();
            }, 1500); // 1.5 seconds of silence means they finished
          }
        }
        
        requestAnimationFrame(checkAudioLevel);
      };
      
      mediaRecorder.start();
      setIsListening(true);
      checkAudioLevel();
      
    } catch (err) {
      console.error("Microphone access denied or failed", err);
    }
  };

  const stopListeningAndProcess = () => {
    setIsListening(false);
    if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
    silenceTimerRef.current = null;
    
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
  };

  const stopEverything = () => {
    setIsListening(false);
    isProcessingRef.current = false;
    if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause();
    }
  };

  const processUserAudio = async (audioBlob: Blob) => {
    isProcessingRef.current = true;
    try {
      // 1. Transcribe with Groq Whisper
      const formData = new FormData();
      formData.append('file', audioBlob, 'speech.webm');
      
      const sttRes = await fetch('http://localhost:8000/api/v1/smart/transcribe', {
        method: 'POST',
        body: formData
      });
      
      if (!sttRes.ok) throw new Error("STT Failed");
      const sttData = await sttRes.json();
      const text = sttData.text;
      
      if (!text || text.trim() === "") {
        // Just breath or noise, ignore and keep listening
        isProcessingRef.current = false;
        startListening();
        return;
      }
      
      addTranscript('user', text);
      
      // 2. Send to Fast-Turn for RAG + LLM + TTS
      const res = await fetch('http://localhost:8000/api/v1/smart/fast-turn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          lead_name: leadName.split(' ')[0],
          history: transcript.map(t => ({ role: t.role === 'agent' ? 'assistant' : 'user', content: t.text }))
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        if (data.reply) addTranscript('agent', data.reply);
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
  };

  const playAudioBase64 = (base64: string): Promise<void> => {
    return new Promise((resolve) => {
      isAgentSpeakingRef.current = true;
      setIsAgentSpeaking(true);
      isProcessingRef.current = false;
      
      const audio = new Audio(base64);
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
  };

  const speakAgentText = async (text: string) => {
    isProcessingRef.current = true;
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
  };

  const endCall = () => {
    stopEverything();
    setCallState('ended');
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md animate-fade-in p-4 md:p-8">
      <div className="w-full max-w-5xl h-[85vh] bg-[#0a0a0a] border border-white/10 rounded-3xl shadow-2xl overflow-hidden flex flex-col md:flex-row">
        
        {/* Left Side: Visualizer */}
        <div className="w-full md:w-[45%] bg-gradient-to-b from-[#1a1a1a] to-black flex flex-col relative border-r border-white/10">
          <div className="p-6 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-[#00e599]/20 flex items-center justify-center text-[#00e599] font-bold border border-[#00e599]/30 shadow-[0_0_15px_rgba(0,229,153,0.2)]">
                A
              </div>
              <div>
                <h2 className="text-white font-bold tracking-wide">Aria AI</h2>
                <p className="text-[10px] text-[#00e599] font-bold uppercase tracking-widest">Live Call Active</p>
              </div>
            </div>
            <div className="px-3 py-1 bg-white/5 border border-white/10 rounded-full text-xs text-white/70 font-mono">
              {formatTime(callDuration)}
            </div>
          </div>
          
          <div className="flex-1 flex flex-col items-center justify-center p-6">
            {callState === 'idle' ? (
              <div className="text-center space-y-6">
                <div className="w-24 h-24 mx-auto rounded-full bg-white/5 border border-white/10 flex items-center justify-center">
                  <Mic size={32} className="text-white/50" />
                </div>
                <h3 className="text-2xl font-bold text-white">Ready to connect?</h3>
                <p className="text-white/50 text-sm max-w-xs mx-auto">This will initiate a live, real-time voice call with Aria, powered by Groq Whisper & Laya Router.</p>
                <Button variant="primary" size="lg" className="px-10 rounded-full shadow-[0_0_20px_rgba(0,229,153,0.3)] hover:scale-105 transition-transform" onClick={() => setCallState('connecting')}>
                  Start Live Voice Call
                </Button>
              </div>
            ) : callState === 'connecting' ? (
              <div className="flex flex-col items-center justify-center animate-pulse">
                <div className="w-24 h-24 rounded-full bg-[#00e599]/10 flex items-center justify-center mb-4">
                  <PhoneCall size={32} className="text-[#00e599]" />
                </div>
                <p className="text-white font-bold tracking-wide">Connecting to Aria...</p>
                <p className="text-xs text-white/50 mt-2">Establishing secure line</p>
              </div>
            ) : callState === 'ended' ? (
              <div className="flex flex-col items-center justify-center">
                <div className="w-24 h-24 rounded-full bg-rose-500/10 flex items-center justify-center mb-4 text-rose-500">
                  <PhoneOff size={32} />
                </div>
                <p className="text-white font-bold tracking-wide">Call Ended</p>
                <p className="text-xs text-white/50 mt-2">Duration: {formatTime(callDuration)}</p>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                {/* Avatar / Visualizer ring */}
                <div className="relative flex items-center justify-center mb-8">
                  <div className={`absolute w-40 h-40 rounded-full border-2 border-[#00e599]/20 ${isAgentSpeaking ? 'animate-ping' : ''}`} />
                  <div className={`absolute w-32 h-32 rounded-full border border-[#00e599]/40 ${isAgentSpeaking ? 'animate-pulse' : ''}`} />
                  
                  <div className={`w-28 h-28 rounded-full bg-[#00e599]/10 border-2 border-[#00e599] flex items-center justify-center shadow-[0_0_30px_rgba(0,229,153,0.3)] z-10 transition-transform duration-300 ${isAgentSpeaking ? 'scale-110' : 'scale-100'}`}>
                    {isAgentSpeaking ? (
                      <Volume2 size={40} className="text-[#00e599] animate-bounce" />
                    ) : isListening ? (
                      <Mic size={40} className="text-white animate-pulse" />
                    ) : (
                      <Sparkles size={32} className="text-white/50" />
                    )}
                  </div>
                </div>

                <div className="text-center">
                  {isAgentSpeaking ? (
                    <p className="text-xs font-bold text-[#00e599] uppercase tracking-widest flex items-center justify-center gap-2">
                      <span className="w-2 h-2 bg-[#00e599] rounded-full animate-ping" />
                      Aria is speaking...
                    </p>
                  ) : isListening ? (
                    <p className="text-xs font-bold text-white uppercase tracking-widest flex items-center justify-center gap-2">
                      <span className="w-2 h-2 bg-rose-500 rounded-full animate-pulse" />
                      Listening... Speak now
                    </p>
                  ) : (
                    <p className="text-xs font-bold text-amber-500 uppercase tracking-widest">
                      Processing response...
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
          
          {callState !== 'ended' && callState !== 'idle' && (
            <div className="p-6 mt-auto flex justify-center z-10">
              <button onClick={endCall} className="w-14 h-14 rounded-full bg-rose-600 hover:bg-rose-500 flex items-center justify-center shadow-lg shadow-rose-600/20 transition-all hover:scale-105">
                <PhoneOff size={24} className="text-white" />
              </button>
            </div>
          )}
        </div>

        {/* Right Side: Transcript & Intelligence */}
        <div className="w-full md:w-[55%] flex flex-col h-full bg-[#111111]">
          <div className="p-4 border-b border-white/10 flex justify-between items-center">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Call Intelligence</h3>
            <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-full text-white/50 hover:text-white transition-colors">
              <X size={18} />
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {callState !== 'ended' ? (
              <div className="space-y-4">
                <div className="inline-block px-3 py-1 bg-white/5 border border-white/10 rounded-lg text-xs text-white/50 font-mono mb-2">
                  Session ID: {Math.random().toString(36).substr(2, 9).toUpperCase()}
                </div>
                
                {transcript.map((item, idx) => (
                  <div key={idx} className={`flex flex-col max-w-[85%] ${item.role === 'agent' ? 'self-start' : 'self-end ml-auto'}`}>
                    <span className="text-[10px] text-white/40 mb-1 ml-1">{item.role === 'agent' ? 'Aria' : leadName} • {item.ts}</span>
                    <div className={`p-3 rounded-2xl text-sm ${
                      item.role === 'agent' 
                        ? 'bg-white/5 border border-white/10 text-white rounded-tl-sm' 
                        : 'bg-[#00e599]/10 border border-[#00e599]/20 text-[#00e599] rounded-tr-sm'
                    }`}>
                      {item.text}
                    </div>
                  </div>
                ))}
                
                {(isAgentSpeaking || isProcessingRef.current) && (
                  <div className={`flex flex-col max-w-[85%] ${isAgentSpeaking ? 'self-start' : 'self-end ml-auto'}`}>
                     <span className="text-[10px] text-white/40 mb-1 ml-1">{isAgentSpeaking ? 'Aria' : leadName}</span>
                     <div className="p-3 rounded-2xl bg-white/5 border border-white/10 text-white/50 text-sm flex items-center gap-2">
                       <div className="flex gap-1">
                         <span className="w-1.5 h-1.5 rounded-full bg-white/50 animate-bounce" style={{ animationDelay: '0ms' }} />
                         <span className="w-1.5 h-1.5 rounded-full bg-white/50 animate-bounce" style={{ animationDelay: '150ms' }} />
                         <span className="w-1.5 h-1.5 rounded-full bg-white/50 animate-bounce" style={{ animationDelay: '300ms' }} />
                       </div>
                     </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-6 animate-fade-in">
                <div className="p-5 rounded-2xl bg-[#00e599]/10 border border-[#00e599]/20">
                  <h4 className="text-[#00e599] font-bold flex items-center gap-2 mb-2">
                    <Sparkles size={16} /> Laya AI Post-Call Summary
                  </h4>
                  <p className="text-white/80 text-sm leading-relaxed">
                    Customer showed high interest in the collection. Handled effectively using the Laya architecture.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
"""

with open(file_path, "w", encoding="utf-8") as f:
    f.write(react_code)

print("Restored Groq Whisper STT + VAD Silence Detection")
