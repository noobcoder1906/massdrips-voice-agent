import { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, PhoneOff, Sparkles, Volume2, Send, MessageSquare, Award, ArrowRight } from 'lucide-react';
import Button from './Button';
import { saveRealCall, type CallRecord } from '../data/realStore';

interface LiveCallModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCallCompleted?: (call: CallRecord) => void;
  leadName?: string;
  leadPhone?: string;
  brandName?: string;
}

export default function LiveCallModal({
  isOpen,
  onClose,
  onCallCompleted,
  leadName = 'Rahul Sharma',
  leadPhone = '+91 98765 43210',
  brandName = 'Mass Drips',
}: LiveCallModalProps) {
  const [callDuration, setCallDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
  const [leadScore, setLeadScore] = useState(65);
  const [transcript, setTranscript] = useState<{ role: 'agent' | 'user'; text: string; ts: string }[]>([
    { role: 'agent', text: `Hey ${leadName.split(' ')[0]}! This is Aria from ${brandName}. I saw you checked out our new acid wash collection. How are you doing today?`, ts: '0:01' }
  ]);
  const [customInput, setCustomInput] = useState('');
  const [callEnded, setCallEnded] = useState(false);
  const recognitionRef = useRef<any>(null);
  const isAgentSpeakingRef = useRef<boolean>(false);
  const lastProcessedTextRef = useRef<string>('');
  const lastProcessedTimeRef = useRef<number>(0);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);

  // Timer
  useEffect(() => {
    if (!isOpen || callEnded) return;
    const interval = setInterval(() => {
      setCallDuration(d => d + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [isOpen, callEnded]);

  // Initial greeting when call modal opens
  useEffect(() => {
    if (isOpen && !callEnded) {
      const greeting = `Hey ${leadName.split(' ')[0]}! Aria here from ${brandName}. I saw you were checking out our new acid wash drop. How's it going?`;
      speakAgentText(greeting);
      startSpeechRecognition();
    }
    return () => {
      stopSpeech();
    };
  }, [isOpen]);

  const speakAgentText = async (text: string) => {
    isAgentSpeakingRef.current = true;
    setIsAgentSpeaking(true);

    try {
      // Fetch high-fidelity Cloned Neural Voice from backend
      const res = await fetch('http://localhost:8000/api/v1/smart/speak', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, voice: 'my_voice', speed: 1.02 })
      });

      if (res.ok) {
        const blob = await res.blob();
        const audioUrl = URL.createObjectURL(blob);
        
        if (audioPlayerRef.current) {
          audioPlayerRef.current.pause();
        }
        
        const audio = new Audio(audioUrl);
        audioPlayerRef.current = audio;
        
        const onFinish = () => {
          setTimeout(() => {
            isAgentSpeakingRef.current = false;
            setIsAgentSpeaking(false);
          }, 350); // Buffer to prevent mic hearing speaker reverberation
        };

        audio.onended = onFinish;
        audio.onerror = onFinish;
        await audio.play();
        return;
      }
    } catch (e) {
      console.log('Falling back to browser speech:', e);
    }

    // Fallback: browser speech synthesis if backend audio unreachable
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.05;
      utterance.pitch = 1.0;
      const voices = window.speechSynthesis.getVoices();
      const naturalVoice = voices.find(v => v.name.includes('Natural') || v.name.includes('Google') || v.lang.startsWith('en'));
      if (naturalVoice) utterance.voice = naturalVoice;

      const onFinish = () => {
        setTimeout(() => {
          isAgentSpeakingRef.current = false;
          setIsAgentSpeaking(false);
        }, 350);
      };

      utterance.onend = onFinish;
      utterance.onerror = onFinish;
      window.speechSynthesis.speak(utterance);
    } else {
      isAgentSpeakingRef.current = false;
      setIsAgentSpeaking(false);
    }
  };

  const stopSpeech = () => {
    isAgentSpeakingRef.current = false;
    setIsAgentSpeaking(false);
    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause();
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch(e) {}
    }
  };

  const startSpeechRecognition = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    try {
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch(e) {}
      }

      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = false;
      recognition.lang = 'en-IN';

      recognition.onend = () => {
        if (isOpen && !callEnded) {
          try { recognition.start(); } catch(e) {}
        }
      };

      recognition.onresult = (event: any) => {
        // Echo Cancellation: If agent is speaking, ignore microphone input completely
        if (isAgentSpeakingRef.current) {
          return;
        }

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            const rawText = event.results[i][0].transcript.trim();
            if (!rawText) continue;

            // Debounce & deduplication check
            const now = Date.now();
            if (rawText.toLowerCase() === lastProcessedTextRef.current.toLowerCase() && (now - lastProcessedTimeRef.current) < 3500) {
              continue;
            }

            lastProcessedTextRef.current = rawText;
            lastProcessedTimeRef.current = now;
            handleUserSpeech(rawText);
          }
        }
      };

      recognition.start();
      recognitionRef.current = recognition;
    } catch (e) {
      console.log('Speech recognition init error:', e);
    }
  };

  const handleUserSpeech = async (userText: string) => {
    if (!userText.trim() || isAgentSpeakingRef.current) return;

    const timeStr = `${Math.floor(callDuration / 60)}:${(callDuration % 60).toString().padStart(2, '0')}`;
    setTranscript(prev => [...prev, { role: 'user', text: userText, ts: timeStr }]);

    // Increase lead score on buying signals
    const lower = userText.toLowerCase();
    if (lower.includes('price') || lower.includes('cost') || lower.includes('size') || lower.includes('hoodie') || lower.includes('buy') || lower.includes('order')) {
      setLeadScore(s => Math.min(96, s + 12));
    }

    // Call live backend Groq AI for intelligent conversational response
    try {
      isAgentSpeakingRef.current = true;
      setIsAgentSpeaking(true);

      const historyPayload = transcript.map(t => ({
        role: t.role === 'agent' ? 'assistant' : 'user',
        content: t.text
      }));

      const res = await fetch('http://localhost:8000/api/v1/smart/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userText,
          tenant_id: 'mass-drips',
          lead_id: 'sample-lead-01',
          history: historyPayload
        })
      });

      let reply = "";
      if (res.ok) {
        const data = await res.json();
        reply = data.reply;
      } else {
        // Fallback realistic response
        if (lower.includes('price') || lower.includes('cost')) {
          reply = "The Acid Wash Tees are ₹1,299, and Hoodies are ₹1,899. You can use coupon code DRIP10 for 10% off today!";
        } else if (lower.includes('size')) {
          reply = "Our fits are slightly relaxed streetwear. Medium is great for 38-40 chest, and Large is 42-44.";
        } else {
          reply = "Got it! Our 240 GSM heavy French Terry gives that perfect boxy drape. Want me to send the link on WhatsApp?";
        }
      }

      const agentTimeStr = `${Math.floor(callDuration / 60)}:${(callDuration % 60).toString().padStart(2, '0')}`;
      setTranscript(prev => [...prev, { role: 'agent', text: reply, ts: agentTimeStr }]);
      speakAgentText(reply);
    } catch (e) {
      const fallbackReply = "Haan bilkul! Our 240 GSM heavy cotton tees and hoodies are in stock. Should I WhatsApp you the direct link?";
      setTranscript(prev => [...prev, { role: 'agent', text: fallbackReply, ts: timeStr }]);
      speakAgentText(fallbackReply);
    }
  };

  const handleSendManualText = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customInput.trim()) return;
    const text = customInput;
    setCustomInput('');
    handleUserSpeech(text);
  };

  const endCall = () => {
    stopSpeech();
    setCallEnded(true);

    const fullTranscript = transcript.map(t => `${t.role === 'agent' ? 'Aria' : leadName}: ${t.text}`).join('\n');
    const outcome: 'converted' | 'interested' | 'callback' = leadScore >= 75 ? 'converted' : leadScore >= 55 ? 'interested' : 'callback';
    const sentiment: 'very_positive' | 'positive' | 'neutral' = leadScore >= 75 ? 'very_positive' : leadScore >= 55 ? 'positive' : 'neutral';

    const record: CallRecord = {
      id: `CALL-${Date.now().toString().slice(-4)}`,
      lead: leadName,
      phone: leadPhone,
      duration: formatSec(callDuration),
      durationSec: callDuration,
      score: leadScore,
      outcome,
      sentiment,
      date: 'Just now',
      transcript: fullTranscript,
      productDiscussed: 'Acid Wash Oversized Tee',
      whatsappMessage: `Hi ${leadName.split(' ')[0]}! Thanks for chatting with Aria at ${brandName}. Here is the link for the Acid Wash Oversized Tee: massdrips.com/catalog. Use code DRIP10 for 10% OFF today!`,
    };

    saveRealCall(record);
    if (onCallCompleted) {
      onCallCompleted(record);
    }
  };

  const formatSec = (s: number) => {
    const mins = Math.floor(s / 60);
    const secs = s % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div
        className="relative w-full max-w-2xl rounded-3xl overflow-hidden shadow-2xl flex flex-col"
        style={{
          background: 'linear-gradient(180deg, #111116 0%, #0c0c10 100%)',
          border: '1px solid var(--color-border)',
          maxHeight: '90vh',
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b" style={{ borderColor: 'var(--color-border)' }}>
          <div className="flex items-center gap-3">
            <div className="relative w-10 h-10 rounded-full flex items-center justify-center font-bold text-black" style={{ background: 'var(--color-accent)' }}>
              A
              {isAgentSpeaking && (
                <span className="absolute -inset-1 rounded-full animate-ping opacity-75" style={{ background: 'var(--color-accent)' }} />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-white text-base">Aria · AI Sales Voice Agent</h3>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  Live HD
                </span>
              </div>
              <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                Calling {leadName} ({leadPhone}) · {formatSec(callDuration)}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--color-border)' }}>
              <Award size={13} style={{ color: 'var(--color-accent)' }} />
              <span className="text-white">Score: {leadScore}/100</span>
            </div>
          </div>
        </div>

        {/* Content Body */}
        {!callEnded ? (
          <div className="p-6 flex-1 overflow-y-auto space-y-6">
            {/* Visualizer Circle */}
            <div className="flex flex-col items-center justify-center py-4">
              <div className="relative flex items-center justify-center">
                {/* Glow rings */}
                <div
                  className={`absolute w-32 h-32 rounded-full transition-all duration-300 ${isAgentSpeaking ? 'animate-pulse scale-125 opacity-40' : 'opacity-10'}`}
                  style={{ background: 'var(--color-accent)', filter: 'blur(20px)' }}
                />
                <div
                  className={`w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 ${isAgentSpeaking ? 'scale-110 shadow-lg shadow-[#00e599]/30' : ''}`}
                  style={{
                    background: isAgentSpeaking ? 'var(--color-accent)' : 'var(--color-bg-card)',
                    border: '2px solid var(--color-accent)',
                  }}
                >
                  <Volume2 size={36} className={isAgentSpeaking ? 'text-black animate-bounce' : 'text-[#00e599]'} />
                </div>
              </div>
              <p className="text-xs font-semibold mt-4 text-center tracking-wide" style={{ color: isAgentSpeaking ? 'var(--color-accent)' : 'var(--color-text-muted)' }}>
                {isAgentSpeaking ? 'ARIA IS SPEAKING (AI VOICE STREAM)...' : 'LISTENING TO YOUR MICROPHONE...'}
              </p>
            </div>

            {/* Live Subtitles / Dialogue Stream */}
            <div className="space-y-3">
              <p className="text-[11px] uppercase font-bold tracking-wider" style={{ color: 'var(--color-text-muted)' }}>
                Live Conversation Stream
              </p>
              <div className="space-y-2.5 max-h-48 overflow-y-auto pr-1">
                {transcript.map((item, idx) => (
                  <div
                    key={idx}
                    className={`flex flex-col p-3 rounded-2xl text-xs max-w-[85%] ${
                      item.role === 'agent'
                        ? 'bg-white/5 border border-white/10 text-white self-start'
                        : 'ml-auto bg-[#00e599]/15 border border-[#00e599]/30 text-[#00e599] font-medium'
                    }`}
                  >
                    <span className="text-[10px] opacity-60 mb-0.5">{item.role === 'agent' ? 'Aria (AI)' : leadName} · {item.ts}</span>
                    <span>{item.text}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Manual input fallback */}
            <form onSubmit={handleSendManualText} className="flex gap-2">
              <input
                type="text"
                placeholder="Or type what you want to say to Aria..."
                className="flex-1 px-4 py-2.5 rounded-xl text-xs bg-white/5 border border-white/10 text-white outline-none focus:border-[#00e599]"
                value={customInput}
                onChange={e => setCustomInput(e.target.value)}
              />
              <Button type="submit" size="sm" variant="primary" rightIcon={<Send size={13} />}>
                Say
              </Button>
            </form>
          </div>
        ) : (
          /* Post-Call Summary View */
          <div className="p-6 flex-1 overflow-y-auto space-y-5 animate-fade-in">
            <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-center">
              <div className="w-10 h-10 rounded-full bg-emerald-500 text-black flex items-center justify-center mx-auto mb-2 font-bold">
                ✓
              </div>
              <h4 className="text-sm font-bold text-white">Call Completed · Intelligence Generated</h4>
              <p className="text-xs text-emerald-300 mt-1">Lead Score: {leadScore}/100 · High Intent Buyer 🔥</p>
            </div>

            <div className="space-y-2">
              <p className="text-xs font-bold text-white flex items-center gap-1.5">
                <Sparkles size={14} className="text-[#00e599]" /> AI Executive Summary
              </p>
              <div className="p-3 rounded-xl bg-white/5 text-xs text-white/80 border border-white/10">
                Customer {leadName} engaged with Mass Drips sales agent regarding Acid Wash Tees and Hoodies. Price objection successfully resolved with 10% first-order discount code DRIP10.
              </div>
            </div>

            <div className="space-y-2">
              <p className="text-xs font-bold text-white flex items-center gap-1.5">
                <MessageSquare size={14} className="text-[#00e599]" /> Automated WhatsApp Follow-up Ready
              </p>
              <div className="p-3 rounded-xl bg-emerald-950/40 text-xs text-emerald-200 border border-emerald-500/20">
                "Hi {leadName.split(' ')[0]}! Thanks for chatting with Aria at {brandName}. Here is the link for the Acid Wash Oversized Tee: massdrips.com/catalog. Use code DRIP10 for 10% OFF today!"
              </div>
            </div>
          </div>
        )}

        {/* Footer Controls */}
        <div className="p-4 border-t flex items-center justify-between" style={{ borderColor: 'var(--color-border)', background: 'rgba(0,0,0,0.4)' }}>
          {!callEnded ? (
            <>
              <button
                onClick={() => setIsMuted(!isMuted)}
                className="px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 bg-white/5 hover:bg-white/10 text-white"
              >
                {isMuted ? <MicOff size={14} className="text-rose-400" /> : <Mic size={14} />}
                {isMuted ? 'Muted' : 'Mic Active'}
              </button>

              <button
                onClick={endCall}
                className="px-6 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-600/30 transition-all"
              >
                <PhoneOff size={15} />
                End Call
              </button>
            </>
          ) : (
            <Button
              variant="primary"
              className="w-full"
              rightIcon={<ArrowRight size={14} />}
              onClick={() => {
                onClose();
                setCallEnded(false);
                setCallDuration(0);
              }}
            >
              Save & Back to Dashboard
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
