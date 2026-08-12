import { useEffect, useRef, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const SCRIPT_ID = 'google-identity-services';

export default function GoogleSignInButton({ onSuccess, onError }) {
  const containerRef = useRef(null);
  const callbackRef = useRef(null);
  const { googleLogin } = useAuth();
  const [loading, setLoading] = useState(false);
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

  callbackRef.current = async ({ credential }) => {
    setLoading(true);
    try {
      const data = await googleLogin(credential);
      onSuccess?.(data);
    } catch (error) {
      onError?.(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!clientId) return undefined;
    const render = () => {
      if (!window.google?.accounts?.id || !containerRef.current) return;
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: (response) => callbackRef.current?.(response),
        auto_select: false,
        cancel_on_tap_outside: true,
      });
      containerRef.current.innerHTML = '';
      window.google.accounts.id.renderButton(containerRef.current, {
        type: 'standard', theme: 'outline', size: 'large',
        text: 'continue_with', shape: 'rectangular', width: 360,
      });
    };

    const existing = document.getElementById(SCRIPT_ID);
    if (existing) {
      if (window.google?.accounts?.id) render();
      else existing.addEventListener('load', render, { once: true });
      return () => existing.removeEventListener('load', render);
    }
    const script = document.createElement('script');
    script.id = SCRIPT_ID;
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = render;
    document.head.appendChild(script);
    return undefined;
  }, [clientId]);

  if (!clientId) {
    return (
      <div className="space-y-2">
        <button
          type="button"
          disabled
          className="w-full h-11 flex items-center justify-center gap-3 rounded-md border border-gray-300 bg-white text-sm font-medium text-gray-500 opacity-75 cursor-not-allowed"
          title="Set VITE_GOOGLE_CLIENT_ID to enable Google sign-in"
        >
          <span className="text-lg font-bold text-blue-600">G</span>
          Continue with Google
        </button>
        <p className="text-center text-xs text-amber-700">
          Google sign-in requires VITE_GOOGLE_CLIENT_ID configuration.
        </p>
      </div>
    );
  }
  return (
    <div className="relative flex justify-center min-h-11">
      <div ref={containerRef} className={loading ? 'opacity-50 pointer-events-none' : ''} />
      {loading && <Loader2 className="absolute right-2 top-2.5 animate-spin text-blue-600" size={20} />}
    </div>
  );
}
