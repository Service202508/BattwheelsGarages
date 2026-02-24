import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { API, AUTH_API } from "@/App";

export default function AuthCallback({ onLogin }) {
  const navigate = useNavigate();
  const hasProcessed = useRef(false);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processSession = async () => {
      const hash = window.location.hash;
      const sessionId = hash.split("session_id=")[1]?.split("&")[0];

      if (!sessionId) {
        navigate("/login", { replace: true });
        return;
      }

      try {
        const response = await fetch(`${AUTH_API}/auth/session`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ session_id: sessionId }),
        });

        if (response.ok) {
          const data = await response.json();
          onLogin(data.user);
          // Clear hash and navigate
          window.history.replaceState(null, "", window.location.pathname);
          navigate("/dashboard", { replace: true, state: { user: data.user } });
        } else {
          navigate("/login", { replace: true });
        }
      } catch (error) {
        console.error("Auth callback error:", error);
        navigate("/login", { replace: true });
      }
    };

    processSession();
  }, [navigate, onLogin]);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary mx-auto mb-4"></div>
        <p className="text-muted-foreground">Authenticating...</p>
      </div>
    </div>
  );
}
