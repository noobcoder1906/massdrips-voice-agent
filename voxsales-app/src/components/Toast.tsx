import React, { createContext, useContext, useState, useCallback } from 'react';
import { X, CheckCircle, AlertTriangle, Info, XCircle } from 'lucide-react';

type ToastType = 'success' | 'error' | 'warning' | 'info';

interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
}

interface ToastContextValue {
  showToast: (type: ToastType, title: string, message?: string) => void;
}

const ToastContext = createContext<ToastContextValue>({ showToast: () => {} });

export const useToast = () => useContext(ToastContext);

const icons = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
};

const colors = {
  success: 'border-l-[#00e599] bg-[#0d2218]',
  error: 'border-l-[#ef4444] bg-[#1f0d0d]',
  warning: 'border-l-[#f59e0b] bg-[#1f1a0d]',
  info: 'border-l-[#6366f1] bg-[#0f0d1f]',
};

const iconColors = {
  success: 'text-[#00e599]',
  error: 'text-[#ef4444]',
  warning: 'text-[#f59e0b]',
  info: 'text-[#6366f1]',
};

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = useCallback((type: ToastType, title: string, message?: string) => {
    const id = Math.random().toString(36).slice(2);
    setToasts(prev => [...prev, { id, type, title, message }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4000);
  }, []);

  const dismiss = (id: string) => setToasts(prev => prev.filter(t => t.id !== id));

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="fixed top-4 right-4 z-[9999] flex flex-col gap-2 w-80">
        {toasts.map((toast) => {
          const Icon = icons[toast.type];
          return (
            <div
              key={toast.id}
              className={`flex items-start gap-3 p-4 rounded-xl border border-white/10 border-l-4 ${colors[toast.type]} animate-slide-in-right shadow-2xl`}
            >
              <Icon size={18} className={`${iconColors[toast.type]} shrink-0 mt-0.5`} />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-white">{toast.title}</p>
                {toast.message && <p className="text-xs text-white/60 mt-0.5">{toast.message}</p>}
              </div>
              <button
                onClick={() => dismiss(toast.id)}
                className="text-white/40 hover:text-white transition-colors shrink-0"
              >
                <X size={14} />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}
