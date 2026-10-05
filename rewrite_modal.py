file_path = r"d:\massdrips-voice-agent\voxsales-app\src\components\LiveCallModal.tsx"
react_code = """import React, { useState, useEffect, useRef } from 'react';
import { X, Mic, Volume2, PhoneOff, ArrowRight, Sparkles, MessageSquare, PhoneCall, AlertCircle } from 'lucide-react';
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
  const [micError, setMicError] = useState<string | null>(null);
  
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  const recognitionRef = useRef<any>(null);
  
  const isAgentSpeakingRef = useRef(false);
  const isProcessingRef = useRef(false);

  const addTranscript = (role: 'user' | 'agent', text: string) => {
    const ts = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setTranscript(prev => [...prev, { role, text, ts }]);
  };

  useEffect(() => {
    let interval: any;
    if (callState === 'connected') {
      interval = setInterval(() => setCallDuration(p => p + 1), 1000);
    }
    return () => clearInterval(interval);
  }, [callState]);

  useEffect(() => {
    // Initialize Web Speech API
    const SpeechRecognition = window.SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true; // Keep listening until we stop it
      recognition.interimResults = false;
      recognition.lang = 'en-IN'; // Indian English for better local accent capture

      recognition.onstart = () => {
        setIsListening(true);
        setMicError(null);
      };

      recognition.onresult = (event: any) => {
        const current = event.resultIndex;
        const text = event.results[current][0].transcript;
        if (text.trim()) {
          // Barge-in: Stop audio if agent is speaking
          if (isAgentSpeakingRef.current && audioPlayerRef.current) {
            audioPlayerRef.current.pause();
            audioPlayerRef.current.currentTime = 0;
            isAgentSpeakingRef.current = false;
            setIsAgentSpeaking(false);
          }
          handleUserSpeech(text);
        }
      };

      recognition.onerror = (event: any) => {
        if (event.error === 'not-allowed') {
          setMicError("Microphone access denied. Please click Allow in your browser URL bar.");
        }
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
        // Auto-restart if we are connected, not processing, and agent is not speaking
        if (callState === 'connected' && !isProcessingRef.current && !isAgentSpeakingRef.current) {
          try { recognition.start(); } catch(e) {}
        }
      };

      recognitionRef.current = recognition;
    } else {
      setMicError("Your browser doesn't support Voice AI natively. Please use Chrome or Edge.");
    }
    
    return () => {
      stopEverything();
    };
  }, [callState]);

  const initCall = async () => {
    setCallState('connecting');
    setMicError(null);
    
    // Request raw mic permission first to ensure browser allows it
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(t => t.stop()); // close immediately, we just wanted permission
    } catch (e) {
      setMicError("You must allow Microphone access for the call to connect.");
      setCallState('idle');
      return;
    }
    
    // Simulate connection time
    setTimeout(() => {
      setCallState('connected');
      startConversation();
    }, 1500);
  };

  const startConversation = async () => {
    const greeting = "Hey there! Sai this side from MASS DRIPS. We are running an exclusive drop right now. What are you looking for today, hoodies or oversized tees?";
    addTranscript('agent', greeting);
    await speakAgentText(greeting);
  };

  const startListening = () => {
    if (callState !== 'connected' || isProcessingRef.current || isAgentSpeakingRef.current) return;
    try {
      recognitionRef.current?.start();
    } catch(e) {}
  };

  const stopListening = () => {
    setIsListening(false);
    try {
      recognitionRef.current?.stop();
    } catch(e) {}
  };

  const handleUserSpeech = async (text: string) => {
    stopListening();
    addTranscript('user', text);
    isProcessingRef.current = true;
    
    try {
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
        if (data.reply) {
           addTranscript('agent', data.reply);
        }
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

  const speakAgentText = async (text: string) => {
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
  };

  const playAudioBase64 = (base64: string): Promise<void> => {
    return new Promise((resolve) => {
      isAgentSpeakingRef.current = true;
      setIsAgentSpeaking(true);
      isProcessingRef.current = false; // We are no longer processing logic, just speaking
      
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

  const stopEverything = () => {
    stopListening();
    isProcessingRef.current = false;
    isAgentSpeakingRef.current = false;
    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause();
    }
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
                <h2 className="text-white font-bold tracking-wide">Sai AI</h2>
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
                {micError && (
                  <div className="flex items-center justify-center gap-2 text-rose-500 text-sm mb-4">
                    <AlertCircle size={16} /> {micError}
                  </div>
                )}
                <Button variant="primary" size="lg" className="px-10 rounded-full shadow-[0_0_20px_rgba(0,229,153,0.3)] hover:scale-105 transition-transform" onClick={initCall}>
                  Start Live Voice Call
                </Button>
              </div>
            ) : callState === 'connecting' ? (
              <div className="flex flex-col items-center justify-center animate-pulse">
                <div className="w-24 h-24 rounded-full bg-[#00e599]/10 flex items-center justify-center mb-4">
                  <PhoneCall size={32} className="text-[#00e599]" />
                </div>
                <p className="text-white font-bold tracking-wide">Connecting to Sai...</p>
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

                <div className="text-center h-10">
                  {micError ? (
                    <p className="text-xs font-bold text-rose-500 uppercase tracking-widest flex items-center justify-center gap-2">
                      <AlertCircle size={14} /> {micError}
                    </p>
                  ) : isAgentSpeaking ? (
                    <p className="text-xs font-bold text-[#00e599] uppercase tracking-widest flex items-center justify-center gap-2">
                      <span className="w-2 h-2 bg-[#00e599] rounded-full animate-ping" />
                      Sai is speaking...
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

        {/* Right Side: Transcript */}
        <div className="w-full md:w-[55%] flex flex-col h-full bg-[#111111]">
          <div className="p-4 border-b border-white/10 flex justify-between items-center">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Live Call Transcript</h3>
            <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-full text-white/50 hover:text-white transition-colors">
              <X size={18} />
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            <div className="inline-block px-3 py-1 bg-white/5 border border-white/10 rounded-lg text-xs text-white/50 font-mono mb-2">
              Secure Local AI Connection
            </div>
            
            {transcript.map((item, idx) => (
              <div key={idx} className={`flex flex-col max-w-[85%] ${item.role === 'agent' ? 'self-start' : 'self-end ml-auto'}`}>
                <span className="text-[10px] text-white/40 mb-1 ml-1">{item.role === 'agent' ? 'Sai' : leadName} • {item.ts}</span>
                <div className={`p-3 rounded-2xl text-sm ${
                  item.role === 'agent' 
                    ? 'bg-white/5 border border-white/10 text-white rounded-tl-sm' 
                    : 'bg-[#00e599]/10 border border-[#00e599]/20 text-[#00e599] rounded-tr-sm'
                }`}>
                  {item.text}
                </div>
              </div>
            ))}
            
            {(isAgentSpeaking || (isProcessingRef.current && !isListening)) && (
              <div className={`flex flex-col max-w-[85%] ${isAgentSpeaking ? 'self-start' : 'self-end ml-auto'}`}>
                 <span className="text-[10px] text-white/40 mb-1 ml-1">{isAgentSpeaking ? 'Sai' : leadName}</span>
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
        </div>
      </div>
    </div>
  );
}
"""

with open(file_path, "w", encoding="utf-8") as f:
    f.write(react_code)
print("LiveCallModal robust rewrite done")
