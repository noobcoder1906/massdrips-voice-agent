import React, { useState, useEffect, useRef } from 'react';
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

export default function LiveCallModal({ isOpen, onClose, onCallCompleted, leadName = 'Customer', brandName = 'MASS DRIPS' }: LiveCallModalProps) {
  if (!isOpen) return null;

  const [callState, setCallState] = useState<'idle' | 'connecting' | 'connected' | 'ended'>('idle');
  const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
  const [transcript, setTranscript] = useState<{ role: 'user' | 'agent', text: string, ts: string }[]>([]);
  const [callDuration, setCallDuration] = useState(0);
  const [micError, setMicError] = useState<string | null>(null);
  const [postCallScore, setPostCallScore] = useState<number | null>(null);
  
  // Audio & WebSocket Refs
  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const audioProcessorRef = useRef<ScriptProcessorNode | null>(null);
  
  // Playback Queue Refs
  const nextPlayTimeRef = useRef<number>(0);
  const activeSourcesRef = useRef<AudioBufferSourceNode[]>([]);

  const stopActiveAudio = () => {
    activeSourcesRef.current.forEach(s => {
      try {
        s.stop();
        s.disconnect();
      } catch (e) {}
    });
    activeSourcesRef.current = [];
    if (audioContextRef.current) {
      nextPlayTimeRef.current = audioContextRef.current.currentTime;
    }
    setIsAgentSpeaking(false);
  };

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

  // Clean up everything when unmounting or closing
  useEffect(() => {
    if (!isOpen) stopEverything();
    return () => stopEverything();
  }, [isOpen]);

  const initCall = async () => {
    setCallState('connecting');
    setMicError(null);
    setTranscript([]);
    setPostCallScore(null);
    
    try {
      // 1. Get Mic Permission & Stream (16kHz mono)
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      });
      audioStreamRef.current = stream;
      
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });
      if (audioCtx.state === 'suspended') {
        await audioCtx.resume();
      }
      audioContextRef.current = audioCtx;
      
      // 2. Connect to the Real-Time Voice Pipeline WebSocket
      // Using generic IDs for demo purposes. Replace with actual tenant/lead IDs if available.
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.port === '5173' ? 'localhost:8000' : window.location.host;
      const wsUrl = `${protocol}//${host}/ws/voice/tenant_123/lead_456`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      
      ws.binaryType = 'arraybuffer'; // Crucial for receiving audio frames
      
      ws.onopen = () => {
        console.log("Live Voice WebSocket Connected!");
        setCallState('connected');
        
        // Start capturing and sending audio
        const source = audioCtx.createMediaStreamSource(stream);
        const processor = audioCtx.createScriptProcessor(4096, 1, 1);
        audioProcessorRef.current = processor;
        
        source.connect(processor);
        processor.connect(audioCtx.destination); // Required for Safari to process audio
        
        processor.onaudioprocess = (e) => {
          if (ws.readyState === WebSocket.OPEN && callState !== 'ended') {
            const inputData = e.inputBuffer.getChannelData(0);
            const pcm16 = new Int16Array(inputData.length);
            for (let i = 0; i < inputData.length; i++) {
              pcm16[i] = Math.max(-32768, Math.min(32767, inputData[i] * 32768));
            }
            ws.send(pcm16.buffer); // Stream raw bytes to VAD/Whisper
          }
        };
      };
      
      ws.onmessage = async (event) => {
        if (typeof event.data === 'string') {
          // JSON Event
          try {
            const msg = JSON.parse(event.data);
            console.log("WS Event:", msg);
            
            if (msg.type === 'interrupt') {
              console.log("⚡ Instant Barge-in: stopping agent speech");
              stopActiveAudio();
            } else if (msg.type === 'transcript') {
              addTranscript('user', msg.text);
            } else if (msg.type === 'agent_text') {
              addTranscript('agent', msg.text);
            } else if (msg.type === 'audio_start') {
              setIsAgentSpeaking(true);
            } else if (msg.type === 'audio_end') {
              setIsAgentSpeaking(false);
            } else if (msg.type === 'call_ended') {
              setPostCallScore(msg.score);
              endCall();
            }
          } catch (err) {
            console.error("Failed to parse WS JSON:", err);
          }
        } else {
          // Binary Audio Frame (TTS chunk)
          playAudioChunk(event.data);
        }
      };
      
      ws.onerror = (e) => {
        console.error("WS Error", e);
        setMicError("WebSocket connection failed. Is the backend running?");
        endCall();
      };
      
      ws.onclose = () => {
        console.log("WS Closed");
        if (callState !== 'ended') endCall();
      };
      
    } catch (e) {
      console.error(e);
      setMicError("Microphone access denied or audio system error.");
      setCallState('idle');
    }
  };

  const playAudioChunk = async (arrayBuffer: ArrayBuffer) => {
    if (!audioContextRef.current) return;
    const audioCtx = audioContextRef.current;
    if (audioCtx.state === 'suspended') {
      await audioCtx.resume();
    }
    
    // Ensure byte alignment for Int16
    const safeBytes = arrayBuffer.byteLength - (arrayBuffer.byteLength % 2);
    if (safeBytes <= 0) return;
    const pcm16 = new Int16Array(arrayBuffer, 0, safeBytes / 2);
    const audioBuffer = audioCtx.createBuffer(1, pcm16.length, 16000);
    const channelData = audioBuffer.getChannelData(0);
    
    for (let i = 0; i < pcm16.length; i++) {
      channelData[i] = pcm16[i] / 32768.0;
    }
    
    const source = audioCtx.createBufferSource();
    source.buffer = audioBuffer;
    
    // Smooth dynamics & anti-clipping limiter (eliminates "bushy" fuzzy sound)
    const gainNode = audioCtx.createGain();
    gainNode.gain.value = 1.0;

    const compressor = audioCtx.createDynamicsCompressor();
    compressor.threshold.value = -6;
    compressor.knee.value = 6;
    compressor.ratio.value = 3;
    compressor.attack.value = 0.003;
    compressor.release.value = 0.05;
    
    source.connect(gainNode);
    gainNode.connect(compressor);
    compressor.connect(audioCtx.destination);
    
    // Playback scheduling to avoid gaps
    const currTime = audioCtx.currentTime;
    if (nextPlayTimeRef.current < currTime) {
      nextPlayTimeRef.current = currTime;
    }
    
    source.start(nextPlayTimeRef.current);
    nextPlayTimeRef.current += audioBuffer.duration;

    activeSourcesRef.current.push(source);
    source.onended = () => {
      activeSourcesRef.current = activeSourcesRef.current.filter(s => s !== source);
    };
  };

  const stopEverything = () => {
    stopActiveAudio();
    if (audioProcessorRef.current) {
      audioProcessorRef.current.disconnect();
      audioProcessorRef.current = null;
    }
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach(t => t.stop());
      audioStreamRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(console.error);
      audioContextRef.current = null;
    }
    if (wsRef.current) {
      if (wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
      wsRef.current = null;
    }
    nextPlayTimeRef.current = 0;
    setIsAgentSpeaking(false);
  };

  const endCall = () => {
    stopEverything();
    setCallState('ended');
    if (onCallCompleted) onCallCompleted();
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
                <p className="text-white font-bold tracking-wide">Connecting WebSocket...</p>
                <p className="text-xs text-white/50 mt-2">Establishing secure pipeline</p>
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
                    ) : (
                      <Mic size={40} className="text-white animate-pulse" />
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
                      Aria is speaking...
                    </p>
                  ) : (
                    <p className="text-xs font-bold text-white uppercase tracking-widest flex items-center justify-center gap-2">
                      <span className="w-2 h-2 bg-[#00e599] rounded-full animate-pulse" />
                      Pipeline Active - Speak Naturally
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
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Live Pipeline Transcript</h3>
            <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-full text-white/50 hover:text-white transition-colors">
              <X size={18} />
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            <div className="inline-block px-3 py-1 bg-white/5 border border-white/10 rounded-lg text-xs text-white/50 font-mono mb-2">
              Status: {callState.toUpperCase()}
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
            
            {callState === 'ended' && postCallScore !== null && (
              <div className="mt-8 p-5 rounded-2xl bg-[#00e599]/10 border border-[#00e599]/20 animate-fade-in">
                <h4 className="text-[#00e599] font-bold flex items-center gap-2 mb-2">
                  <Sparkles size={16} /> Laya AI Post-Call Score
                </h4>
                <div className="flex items-center gap-4">
                  <div className="text-4xl font-bold text-white">{postCallScore}/100</div>
                  <p className="text-white/80 text-sm leading-relaxed">
                    Lead successfully qualified via Laya Router pipeline.
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
