import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Mail, Lock, User, Eye, EyeOff, Zap } from "lucide-react";
import { API } from "@/App";

// ─── Inject fonts + keyframes once ───────────────────────────────────────────
function useLoginStyles() {
  useEffect(() => {
    if (!document.getElementById("bw-font")) {
      const link = document.createElement("link");
      link.id = "bw-font";
      link.rel = "stylesheet";
      link.href =
        "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=DM+Serif+Display&family=Syne:wght@400;500;600;700&display=swap";
      document.head.appendChild(link);
    }
    if (!document.getElementById("bw-css")) {
      const s = document.createElement("style");
      s.id = "bw-css";
      s.textContent = `
        @keyframes bwFadeUp {
          from { opacity: 0; transform: translateY(16px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes bwPulse {
          0%, 100% { opacity: 1; }
          50%       { opacity: 0.4; }
        }
        @keyframes bwSpin {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
        .bw-input::placeholder { color: rgba(244,246,240,0.25) !important; }
        .bw-input { caret-color: #C8FF00; }
        .bw-input:-webkit-autofill,
        .bw-input:-webkit-autofill:hover,
        .bw-input:-webkit-autofill:focus {
          -webkit-box-shadow: 0 0 0 1000px #080C0F inset !important;
          -webkit-text-fill-color: #F4F6F0 !important;
        }
        .bw-forgot { transition: color 0.15s; }
        .bw-forgot:hover { color: #C8FF00 !important; }
        .bw-footer-link {
          color: rgba(244,246,240,0.35);
          text-decoration: none;
          font-family: 'Syne', sans-serif;
          font-size: 11px;
          transition: color 0.15s;
        }
        .bw-footer-link:hover { color: rgba(200,255,0,0.60); }
        .bw-google-btn:hover {
          background: rgba(255,255,255,0.07) !important;
          border-color: rgba(255,255,255,0.18) !important;
          color: #F4F6F0 !important;
        }
        .bw-cta-btn:not(:disabled):hover {
          background: rgba(200,255,0,0.88) !important;
          transform: translateY(-1px) !important;
          box-shadow: 0 4px 20px rgba(200,255,0,0.20) !important;
        }
        @media (max-width: 767px) {
          .bw-left-panel  { display: none !important; }
          .bw-mobile-bar  { display: flex !important; }
          .bw-right-panel { width: 100% !important; padding: 72px 24px 80px !important; }
          .bw-form-wrap   { max-width: 100% !important; }
        }
        @media (min-width: 768px) and (max-width: 1023px) {
          .bw-left-panel  { width: 45% !important; }
          .bw-right-panel { width: 55% !important; }
          .bw-headline    { font-size: 40px !important; }
          .bw-stats-strip { display: none !important; }
        }
      `;
      document.head.appendChild(s);
    }
  }, []);
}

// ─── Animation helper ─────────────────────────────────────────────────────────
const anim = (delay) => ({
  animation: `bwFadeUp 0.45s ease ${delay}ms both`,
});

// ─── Google G icon ────────────────────────────────────────────────────────────
const GoogleIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true">
    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
  </svg>
);

// ─── Spinner ──────────────────────────────────────────────────────────────────
const Spinner = () => (
  <svg
    style={{ width: 16, height: 16, animation: "bwSpin 0.8s linear infinite" }}
    viewBox="0 0 24 24"
    fill="none"
  >
    <circle cx="12" cy="12" r="10" stroke="rgba(8,12,15,0.3)" strokeWidth="3" />
    <path d="M12 2a10 10 0 0 1 10 10" stroke="#080C0F" strokeWidth="3" strokeLinecap="round" />
  </svg>
);

// ─── FormInput ────────────────────────────────────────────────────────────────
const FormInput = ({
  icon: Icon,
  type,
  id,
  label,
  placeholder,
  value,
  onChange,
  required,
  showToggle,
  dataTestId,
}) => {
  const [show, setShow] = useState(false);
  const [focused, setFocused] = useState(false);
  const inputType = showToggle ? (show ? "text" : "password") : type;

  return (
    <div>
      <label
        htmlFor={id}
        style={{
          display: "block",
          marginBottom: 6,
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 10,
          fontWeight: 500,
          letterSpacing: "0.10em",
          color: "rgba(244,246,240,0.40)",
          textTransform: "uppercase",
        }}
      >
        {label}
      </label>
      <div style={{ position: "relative" }}>
        {/* Left icon */}
        <div
          style={{
            position: "absolute",
            left: 14,
            top: "50%",
            transform: "translateY(-50%)",
            color: focused ? "rgba(200,255,0,0.50)" : "rgba(244,246,240,0.25)",
            transition: "color 0.15s",
            pointerEvents: "none",
            display: "flex",
            alignItems: "center",
          }}
        >
          <Icon size={16} />
        </div>

        <input
          id={id}
          className="bw-input"
          type={inputType}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          required={required}
          data-testid={dataTestId}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          style={{
            width: "100%",
            height: 44,
            background: focused ? "rgba(200,255,0,0.03)" : "rgba(255,255,255,0.04)",
            border: `1px solid ${focused ? "rgba(200,255,0,0.50)" : "rgba(255,255,255,0.10)"}`,
            borderRadius: 4,
            padding: `0 ${showToggle ? 44 : 14}px 0 40px`,
            fontFamily: "'Syne', sans-serif",
            fontSize: 14,
            color: "#F4F6F0",
            outline: "none",
            boxShadow: focused ? "0 0 0 3px rgba(200,255,0,0.08)" : "none",
            transition: "border-color 0.15s, box-shadow 0.15s, background 0.15s",
          }}
        />

        {/* Eye toggle */}
        {showToggle && (
          <button
            type="button"
            onClick={() => setShow((v) => !v)}
            style={{
              position: "absolute",
              right: 14,
              top: "50%",
              transform: "translateY(-50%)",
              background: "none",
              border: "none",
              cursor: "pointer",
              color: "rgba(244,246,240,0.25)",
              display: "flex",
              alignItems: "center",
              padding: 0,
              transition: "color 0.15s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "rgba(244,246,240,0.60)")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "rgba(244,246,240,0.25)")}
          >
            {show ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        )}
      </div>
    </div>
  );
};

// ─── CTA Button ───────────────────────────────────────────────────────────────
const CTAButton = ({ isLoading, children, dataTestId }) => (
  <button
    type="submit"
    disabled={isLoading}
    data-testid={dataTestId}
    className="bw-cta-btn"
    style={{
      width: "100%",
      height: 44,
      background: "#C8FF00",
      color: "#080C0F",
      border: "none",
      borderRadius: 4,
      fontFamily: "'JetBrains Mono', monospace",
      fontSize: 13,
      fontWeight: 700,
      letterSpacing: "0.08em",
      textTransform: "uppercase",
      cursor: isLoading ? "not-allowed" : "pointer",
      opacity: isLoading ? 0.6 : 1,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      gap: 8,
      transition: "all 0.15s ease",
      pointerEvents: isLoading ? "none" : "auto",
    }}
  >
    {isLoading ? (
      <>
        <Spinner />
        Authenticating...
      </>
    ) : (
      children
    )}
  </button>
);

// ─── Inline error ─────────────────────────────────────────────────────────────
const InlineError = ({ msg }) =>
  msg ? (
    <div
      style={{
        marginTop: 10,
        background: "rgba(255,59,47,0.08)",
        border: "1px solid rgba(255,59,47,0.25)",
        borderLeft: "3px solid #FF3B2F",
        borderRadius: 4,
        padding: "10px 14px",
        fontFamily: "'Syne', sans-serif",
        fontSize: 13,
        color: "#FF3B2F",
      }}
    >
      {msg}
    </div>
  ) : null;

// ─── OR Divider ───────────────────────────────────────────────────────────────
const OrDivider = () => (
  <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "24px 0 0" }}>
    <div style={{ flex: 1, height: 1, background: "rgba(255,255,255,0.07)" }} />
    <span
      style={{
        fontFamily: "'Syne', sans-serif",
        fontSize: 12,
        color: "rgba(244,246,240,0.30)",
        whiteSpace: "nowrap",
      }}
    >
      or
    </span>
    <div style={{ flex: 1, height: 1, background: "rgba(255,255,255,0.07)" }} />
  </div>
);

// ─── Grain SVG data URL ───────────────────────────────────────────────────────
const GRAIN = `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)'/%3E%3C/svg%3E")`;

// ─── Left Panel ───────────────────────────────────────────────────────────────
const LeftPanel = () => (
  <div
    className="bw-left-panel"
    style={{
      width: "55%",
      position: "relative",
      overflow: "hidden",
      background: "#080C0F",
      borderRight: "1px solid rgba(255,255,255,0.06)",
      flexShrink: 0,
    }}
  >
    {/* Layer 1 — grid */}
    <div
      style={{
        position: "absolute",
        inset: 0,
        backgroundImage: `
          linear-gradient(rgba(200,255,0,0.03) 1px, transparent 1px),
          linear-gradient(90deg, rgba(200,255,0,0.03) 1px, transparent 1px)`,
        backgroundSize: "40px 40px",
      }}
    />

    {/* Layer 2 — ambient glows */}
    <div
      style={{
        position: "absolute",
        inset: 0,
        background: `
          radial-gradient(ellipse 600px 400px at 20% 30%, rgba(200,255,0,0.07) 0%, transparent 70%),
          radial-gradient(ellipse 400px 400px at 80% 80%, rgba(26,255,228,0.04) 0%, transparent 70%)`,
      }}
    />

    {/* Layer 3 — grain */}
    <div
      style={{
        position: "absolute",
        inset: 0,
        backgroundImage: GRAIN,
        opacity: 0.025,
        mixBlendMode: "overlay",
        pointerEvents: "none",
      }}
    />

    {/* Content */}
    <div
      style={{
        position: "relative",
        zIndex: 10,
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        padding: "64px 64px 140px",
      }}
    >
      {/* Logo mark */}
      <div style={anim(0)}>
        <div
          style={{
            width: 48,
            height: 48,
            background: "rgba(200,255,0,0.08)",
            border: "1px solid rgba(200,255,0,0.25)",
            borderRadius: 4,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 0 20px rgba(200,255,0,0.15), inset 0 0 20px rgba(200,255,0,0.05)",
          }}
        >
          <Zap size={24} color="#C8FF00" />
        </div>
      </div>

      {/* Product name */}
      <div style={{ marginTop: 12, ...anim(80) }}>
        <span
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 11,
            fontWeight: 600,
            letterSpacing: "0.20em",
            color: "rgba(244,246,240,0.40)",
            textTransform: "uppercase",
          }}
        >
          BATTWHEELS OS
        </span>
      </div>

      {/* Eyebrow */}
      <div style={{ marginTop: 48, ...anim(120) }}>
        <span
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 10,
            fontWeight: 500,
            letterSpacing: "0.16em",
            color: "#C8FF00",
            textTransform: "uppercase",
          }}
        >
          EV FAILURE INTELLIGENCE
        </span>
      </div>

      {/* Headline */}
      <div style={{ marginTop: 16, ...anim(180) }}>
        <h1
          className="bw-headline"
          style={{
            fontFamily: "'DM Serif Display', serif",
            fontSize: 52,
            fontWeight: 400,
            lineHeight: 1.1,
            color: "#F4F6F0",
            letterSpacing: "-0.02em",
            margin: 0,
          }}
        >
          Every breakdown.
          <br />
          Resolved{" "}
          <span style={{ color: "#C8FF00" }}>smarter.</span>
        </h1>
      </div>

      {/* Sub-headline */}
      <div style={{ marginTop: 20, ...anim(240) }}>
        <p
          style={{
            fontFamily: "'Syne', sans-serif",
            fontSize: 15,
            fontWeight: 400,
            lineHeight: 1.65,
            color: "rgba(244,246,240,0.50)",
            maxWidth: 380,
            margin: 0,
          }}
        >
          AI-powered diagnostics for Electric 2W, 3W &amp; 4W vehicles —
          turning every failure into reusable enterprise intelligence.
        </p>
      </div>
    </div>

    {/* Stats strip */}
    <div
      className="bw-stats-strip"
      style={{
        position: "absolute",
        bottom: 48,
        left: 64,
        right: 64,
        display: "flex",
        alignItems: "center",
        zIndex: 10,
        ...anim(320),
      }}
    >
      {/* Stat 1 */}
      <div style={{ flex: 1 }}>
        <div
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 14,
            color: "#C8FF00",
            marginBottom: 4,
          }}
        >
          2W · 3W · 4W
        </div>
        <div
          style={{
            fontFamily: "'Syne', sans-serif",
            fontSize: 11,
            color: "rgba(244,246,240,0.40)",
          }}
        >
          Vehicle Categories
        </div>
      </div>

      <div
        style={{
          width: 1,
          height: 36,
          background: "rgba(255,255,255,0.08)",
          margin: "0 24px",
          flexShrink: 0,
        }}
      />

      {/* Stat 2 */}
      <div style={{ flex: 1 }}>
        <div
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 14,
            color: "#C8FF00",
            marginBottom: 4,
          }}
        >
          EFI
        </div>
        <div
          style={{
            fontFamily: "'Syne', sans-serif",
            fontSize: 11,
            color: "rgba(244,246,240,0.40)",
          }}
        >
          Failure Intelligence
        </div>
      </div>

      <div
        style={{
          width: 1,
          height: 36,
          background: "rgba(255,255,255,0.08)",
          margin: "0 24px",
          flexShrink: 0,
        }}
      />

      {/* Stat 3 — live indicator */}
      <div style={{ flex: 1 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              background: "#22C55E",
              boxShadow: "0 0 8px #22C55E",
              animation: "bwPulse 2s infinite",
              flexShrink: 0,
            }}
          />
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 11,
              color: "rgba(244,246,240,0.40)",
            }}
          >
            System Operational
          </span>
        </div>
      </div>
    </div>
  </div>
);

// ─── Main export ──────────────────────────────────────────────────────────────
export default function Login({ onLogin }) {
  useLoginStyles();

  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("login");
  const [loginError, setLoginError] = useState("");
  const [registerError, setRegisterError] = useState("");
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotSent, setForgotSent] = useState(false);
  const [forgotLoading, setForgotLoading] = useState(false);
  const [loginData, setLoginData] = useState({ email: "", password: "" });
  const [registerData, setRegisterData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  // ── Auth handlers (logic unchanged) ────────────────────────────────────────
  const handleGoogleLogin = () => {
    const redirectUrl = window.location.origin + "/dashboard";
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setLoginError("");
    try {
      const response = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(loginData),
      });
      const data = await response.json();
      if (response.ok) {
        const orgs = data.organizations || [];
        if (data.organization) {
          localStorage.setItem("organization_id", data.organization.organization_id);
          localStorage.setItem("organization", JSON.stringify(data.organization));
        }
        await onLogin(data.user, data.token, orgs);
        toast.success("Welcome back!");
        if (data.user?.is_platform_admin) {
          navigate("/platform-admin", { replace: true });
        } else if (orgs.length <= 1) {
          navigate("/dashboard", { replace: true });
        }
      } else {
        const msg = data.detail || "Login failed";
        setLoginError(msg);
        toast.error(msg);
      }
    } catch {
      const msg = "Network error. Please try again.";
      setLoginError(msg);
      toast.error(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleForgotPassword = async () => {
    if (!forgotEmail) {
      toast.error("Please enter your email address");
      return;
    }
    setForgotLoading(true);
    try {
      const res = await fetch(`${API}/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: forgotEmail }),
      });
      if (res.ok) {
        setForgotSent(true);
        toast.success("If an account exists, a reset link has been sent");
      } else {
        toast.error("Something went wrong. Please try again.");
      }
    } catch {
      toast.error("Network error. Please try again.");
    } finally {
      setForgotLoading(false);
    }
  };


  const handleRegister = async (e) => {
    e.preventDefault();
    if (registerData.password !== registerData.confirmPassword) {
      const msg = "Passwords do not match";
      setRegisterError(msg);
      toast.error(msg);
      return;
    }
    setIsLoading(true);
    setRegisterError("");
    try {
      const response = await fetch(`${API}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: registerData.name,
          email: registerData.email,
          password: registerData.password,
          role: "customer",
        }),
      });
      const data = await response.json();
      if (response.ok) {
        toast.success("Account created! Please login.");
        setRegisterData({ name: "", email: "", password: "", confirmPassword: "" });
        setActiveTab("login");
      } else {
        const msg = data.detail || "Registration failed";
        setRegisterError(msg);
        toast.error(msg);
      }
    } catch {
      const msg = "Network error. Please try again.";
      setRegisterError(msg);
      toast.error(msg);
    } finally {
      setIsLoading(false);
    }
  };

  // ── Tab switcher ────────────────────────────────────────────────────────────
  const switchTab = (tab) => {
    setActiveTab(tab);
    setLoginError("");
    setRegisterError("");
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#080C0F", overflow: "hidden" }}>

      {/* Mobile top bar */}
      <div
        className="bw-mobile-bar"
        style={{
          display: "none",
          position: "fixed",
          top: 0, left: 0, right: 0,
          height: 56,
          background: "#080C0F",
          borderBottom: "1px solid rgba(255,255,255,0.07)",
          alignItems: "center",
          justifyContent: "center",
          gap: 10,
          zIndex: 100,
        }}
      >
        <div
          style={{
            width: 28, height: 28,
            background: "rgba(200,255,0,0.08)",
            border: "1px solid rgba(200,255,0,0.25)",
            borderRadius: 4,
            display: "flex", alignItems: "center", justifyContent: "center",
          }}
        >
          <Zap size={14} color="#C8FF00" />
        </div>
        <span
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 11, fontWeight: 600,
            letterSpacing: "0.20em",
            color: "rgba(244,246,240,0.40)",
            textTransform: "uppercase",
          }}
        >
          BATTWHEELS OS
        </span>
      </div>

      {/* Left panel */}
      <LeftPanel />

      {/* Right panel */}
      <div
        className="bw-right-panel"
        style={{
          width: "45%",
          position: "relative",
          background: "#080C0F",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          minHeight: "100vh",
          padding: "80px 56px",
        }}
      >
        {/* Form wrapper */}
        <div
          className="bw-form-wrap"
          style={{
            width: "100%",
            maxWidth: 360,
          }}
        >
          {/* Header */}
          <div style={anim(100)}>
            <h2
              style={{
                fontFamily: "'DM Serif Display', serif",
                fontSize: 28,
                fontWeight: 400,
                color: "#F4F6F0",
                letterSpacing: "-0.01em",
                margin: 0,
                lineHeight: 1.2,
              }}
            >
              {activeTab === "login" ? "Welcome back" : "Create your account"}
            </h2>
            <p
              style={{
                fontFamily: "'Syne', sans-serif",
                fontSize: 14,
                color: "rgba(244,246,240,0.45)",
                marginTop: 4,
                marginBottom: 0,
              }}
            >
              {activeTab === "login"
                ? "Sign in to your workspace"
                : "Start your free trial today"}
            </p>
          </div>

          {/* Tabs */}
          <div style={{ marginTop: 32, ...anim(180) }}>
            <div
              style={{
                display: "flex",
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.07)",
                borderRadius: 4,
                padding: 3,
                gap: 3,
              }}
            >
              {["login", "register"].map((tab) => (
                <button
                  key={tab}
                  type="button"
                  data-testid={`${tab}-tab`}
                  onClick={() => switchTab(tab)}
                  style={{
                    flex: 1,
                    height: 34,
                    border: activeTab === tab
                      ? "1px solid rgba(200,255,0,0.25)"
                      : "1px solid transparent",
                    borderRadius: 2,
                    background: activeTab === tab ? "rgba(200,255,0,0.10)" : "transparent",
                    color: activeTab === tab ? "#C8FF00" : "rgba(244,246,240,0.40)",
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: 12,
                    fontWeight: activeTab === tab ? 600 : 400,
                    letterSpacing: "0.06em",
                    textTransform: "uppercase",
                    cursor: "pointer",
                    transition: "all 0.15s",
                  }}
                >
                  {tab === "login" ? "LOGIN" : "REGISTER"}
                </button>
              ))}
            </div>
          </div>

          {/* ── LOGIN FORM ─────────────────────────────────────────────── */}
          {activeTab === "login" && (
            <form onSubmit={handleLogin}>
              <div
                style={{
                  marginTop: 28,
                  display: "flex",
                  flexDirection: "column",
                  gap: 14,
                }}
              >
                <div style={anim(240)}>
                  <FormInput
                    icon={Mail}
                    type="email"
                    id="login-email"
                    label="Email"
                    placeholder="you@example.com"
                    value={loginData.email}
                    onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                    required
                    dataTestId="login-email-input"
                  />
                </div>
                <div style={anim(290)}>
                  <FormInput
                    icon={Lock}
                    type="password"
                    id="login-password"
                    label="Password"
                    placeholder="••••••••"
                    value={loginData.password}
                    onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                    required
                    showToggle
                    dataTestId="login-password-input"
                  />
                </div>
              </div>

              {/* Forgot password */}
              <div style={{ textAlign: "right", marginTop: 8, ...anim(320) }}>
                <span
                  className="bw-forgot"
                  onClick={() => { setForgotEmail(loginData.email); setForgotSent(false); setShowForgotPassword(true); }}
                  style={{
                    fontFamily: "'Syne', sans-serif",
                    fontSize: 12,
                    color: "rgba(200,255,0,0.60)",
                    cursor: "pointer",
                  }}
                  data-testid="forgot-password-link"
                >
                  Forgot password?
                </span>
              </div>

              {/* CTA */}
              <div style={{ marginTop: 24, ...anim(360) }}>
                <CTAButton isLoading={isLoading} dataTestId="login-submit-btn">
                  SIGN IN →
                </CTAButton>
                <InlineError msg={loginError} />
              </div>

              {/* Divider + Google */}
              <div style={anim(400)}>
                <OrDivider />
                <div style={{ marginTop: 16 }}>
                  <button
                    type="button"
                    onClick={handleGoogleLogin}
                    data-testid="google-login-btn"
                    className="bw-google-btn"
                    style={{
                      width: "100%",
                      height: 44,
                      background: "rgba(255,255,255,0.04)",
                      border: "1px solid rgba(255,255,255,0.10)",
                      borderRadius: 4,
                      fontFamily: "'Syne', sans-serif",
                      fontSize: 14,
                      color: "rgba(244,246,240,0.70)",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: 10,
                      transition: "all 0.15s",
                    }}
                  >
                    <GoogleIcon />
                    Continue with Google
                  </button>
                </div>
              </div>
            </form>
          )}

          {/* ── REGISTER FORM ───────────────────────────────────────────── */}
          {activeTab === "register" && (
            <form onSubmit={handleRegister}>
              <div
                style={{
                  marginTop: 28,
                  display: "flex",
                  flexDirection: "column",
                  gap: 14,
                }}
              >
                <FormInput
                  icon={User}
                  type="text"
                  id="register-name"
                  label="Full Name"
                  placeholder="John Doe"
                  value={registerData.name}
                  onChange={(e) => setRegisterData({ ...registerData, name: e.target.value })}
                  required
                  dataTestId="register-name-input"
                />
                <FormInput
                  icon={Mail}
                  type="email"
                  id="register-email"
                  label="Email"
                  placeholder="you@example.com"
                  value={registerData.email}
                  onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
                  required
                  dataTestId="register-email-input"
                />
                <FormInput
                  icon={Lock}
                  type="password"
                  id="register-password"
                  label="Password"
                  placeholder="••••••••"
                  value={registerData.password}
                  onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
                  required
                  showToggle
                  dataTestId="register-password-input"
                />
                <FormInput
                  icon={Lock}
                  type="password"
                  id="register-confirm"
                  label="Confirm Password"
                  placeholder="••••••••"
                  value={registerData.confirmPassword}
                  onChange={(e) =>
                    setRegisterData({ ...registerData, confirmPassword: e.target.value })
                  }
                  required
                  showToggle
                  dataTestId="register-confirm-input"
                />
              </div>

              <div style={{ marginTop: 24 }}>
                <CTAButton isLoading={isLoading} dataTestId="register-submit-btn">
                  CREATE ACCOUNT →
                </CTAButton>
                <InlineError msg={registerError} />
              </div>
            </form>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            position: "absolute",
            bottom: 32,
            left: 0,
            right: 0,
            textAlign: "center",
            padding: "0 56px",
          }}
        >
          <p
            style={{
              fontFamily: "'Syne', sans-serif",
              fontSize: 11,
              color: "rgba(244,246,240,0.25)",
              margin: "0 0 6px",
            }}
          >
            © 2026 Battwheels Services Pvt. Ltd.
          </p>
          <div style={{ display: "flex", justifyContent: "center", gap: 12, alignItems: "center" }}>
            <a href="#" className="bw-footer-link">
              Privacy Policy
            </a>
            <span style={{ color: "rgba(244,246,240,0.15)", fontSize: 11 }}>·</span>
            <a href="#" className="bw-footer-link">
              Terms of Service
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
