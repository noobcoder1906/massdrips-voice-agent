import sys

file_path = r"d:\massdrips-voice-agent\voxsales-app\src\components\LiveCallModal.tsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

new_content = """import React, { useState, useEffect, useRef } from 'react';
import { X, Mic, Volume2, PhoneOff, ArrowRight, Sparkles, MessageSquare, PhoneCall } from 'lucide-react';
import Button from './Button';

interface LiveCallModalProps {
  onClose: () => void;
  leadName?: string;
  brandName?: string;
}

export default function LiveCallModal({ onClose, leadName = 'Customer', brandName = 'MASS DRIPS' }: LiveCallModalProps) {
  const [callState, setCallState] = useState<'idle' | 'connecting' | 'connected' | 'ended'>('idle');
  const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState<{ role: 'user' | 'agent', text: string, ts: string }[]>([]);
  const [callDuration, setCallDuration] = useState(0);
  
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  const recognitionRef = useRef<any>(null);
  
  useEffect(() => {
    // Start "connecting" automatically
    setCallState('connecting');
    const timer = setTimeout(() => {
      setCallState('connected');
      // Greet first
      startConversation();
    }, 2000);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    let interval: any;
    if (callState === 'connected') {
      interval = setInterval(() => setCallDuration(c => c + 1), 1000);
    }
    return () => clearInterval(interval);
  }, [callState]);

  useEffect(() => {
    // Setup Speech Recognition
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-IN';
      
      recognition.onresult = (event: any) => {
        const text = event.results[0][0].transcript;
        if (text.trim()) {
          handleUserSpeech(text);
        }
      };
      
      recognition.onend = () => {
        // If connected, not speaking, we should keep listening
        if (callState === 'connected' && !isAgentSpeakingRef.current && !isProcessingRef.current) {
          try { recognition.start(); } catch(e) {}
        } else {
          setIsListening(false);
        }
      };
      
      recognition.onerror = (e: any) => {
        console.error('Speech recognition error', e);
        setIsListening(false);
      };
      
      recognitionRef.current = recognition;
    }
    
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (audioPlayerRef.current) {
        audioPlayerRef.current.pause();
      }
    };
  }, [callState]);

  // Use refs to avoid closure stale state in onend
  const isAgentSpeakingRef = useRef(false);
  const isProcessingRef = useRef(false);
  
  const addTranscript = (role: 'user' | 'agent', text: string) => {
    const ts = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setTranscript(prev => [...prev, { role, text, ts }]);
  };

  const startConversation = async () => {
    const greeting = "Hey there! Sai this side from MASS DRIPS. We are running an exclusive drop right now. What are you looking for today, hoodies or oversized tees?";
    addTranscript('agent', greeting);
    await speakAgentText(greeting);
  };

  const startListening = () => {
    if (callState !== 'connected' || isAgentSpeakingRef.current || isProcessingRef.current) return;
    try {
      setIsListening(true);
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
      const data = await res.json();
      
      if (data.reply) {
        addTranscript('agent', data.reply);
      }
      
      if (data.audio_base64) {
        await playAudioBase64(data.audio_base64);
      } else {
        isProcessingRef.current = false;
        startListening();
      }
    } catch (e) {
      console.error(e);
      isProcessingRef.current = false;
      startListening();
    }
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
        console.error("Play error:", e);
        isAgentSpeakingRef.current = false;
        setIsAgentSpeaking(false);
        startListening();
        resolve();
      });
    });
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
            console.error("Play error:", e);
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
  };

  const endCall = () => {
    setCallState('ended');
    stopListening();
    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause();
    }
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" onClick={callState === 'ended' ? onClose : undefined} />
      
      <div className="relative w-full max-w-4xl bg-[#111111] border border-white/10 rounded-3xl shadow-2xl overflow-hidden flex flex-col md:flex-row h-[600px] animate-scale-up">
        
        {/* Left Side: Call Interface */}
        <div className="w-full md:w-[45%] flex flex-col border-r border-white/10 relative overflow-hidden" style={{ background: 'linear-gradient(180deg, #1a1a1a 0%, #0d0d0d 100%)' }}>
          
          {/* Header */}
          <div className="p-5 flex items-center justify-between z-10">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-[#00e599]/20 flex items-center justify-center border border-[#00e599]/30">
                <Volume2 size={18} className="text-[#00e599]" />
              </div>
              <div>
                <h3 className="text-white font-bold text-sm tracking-wide">Sai AI</h3>
                <p className="text-[10px] text-[#00e599] font-medium uppercase tracking-wider">{callState === 'connecting' ? 'Connecting...' : callState === 'connected' ? 'Live Call Active' : 'Call Ended'}</p>
              </div>
            </div>
            {callState === 'connected' && (
              <div className="px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-mono text-white/70">
                {formatTime(callDuration)}
              </div>
            )}
          </div>

          {/* Main Visualizer Area */}
          <div className="flex-1 flex flex-col items-center justify-center z-10 p-6">
            
            {callState === 'connecting' ? (
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
          
          {/* End Call Button */}
          {callState !== 'ended' && (
            <div className="p-6 mt-auto flex justify-center z-10">
              <button
                onClick={endCall}
                className="w-14 h-14 rounded-full bg-rose-600 hover:bg-rose-500 flex items-center justify-center shadow-lg shadow-rose-600/20 transition-all hover:scale-105"
              >
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
                
                {(isAgentSpeaking || isListening || isProcessingRef.current) && (
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
            ) : (
              <div className="space-y-6 animate-fade-in">
                <div className="p-5 rounded-2xl bg-[#00e599]/10 border border-[#00e599]/20">
                  <h4 className="text-[#00e599] font-bold flex items-center gap-2 mb-2">
                    <Sparkles size={16} /> Laya AI Post-Call Summary
                  </h4>
                  <p className="text-white/80 text-sm leading-relaxed">
                    Customer showed high interest in the collection. Asked about pricing and stock availability. Handled effectively using the DRIP10 promo code strategy.
                  </p>
                </div>
                
                <div className="p-5 rounded-2xl bg-white/5 border border-white/10">
                  <h4 className="text-white font-bold flex items-center gap-2 mb-3">
                    <MessageSquare size={16} /> Automated Follow-up
                  </h4>
                  <div className="p-3 rounded-xl bg-black/50 text-xs text-white/70 font-mono">
                    "Hi {leadName.split(' ')[0]}! Sai from MASS DRIPS here. As discussed, here's the link to our catalog: massdrips.shop. Use code DRIP10 for 10% off your first order!"
                  </div>
                  <Button variant="primary" size="sm" className="w-full mt-4" rightIcon={<ArrowRight size={14} />} onClick={onClose}>
                    Approve & Send WhatsApp
                  </Button>
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
    f.write(new_content)

print("LiveCallModal.tsx rewritten successfully.")
