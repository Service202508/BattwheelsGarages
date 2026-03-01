import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Check, Eye, EyeOff, ChevronRight, ChevronLeft, Zap } from "lucide-react";
import { toast } from "sonner";
import { API } from "@/App";

const FEATURES = [
  "AI-powered EFI diagnostics",
  "GST-compliant invoicing",
  "Multi-technician management",
  "Customer satisfaction tracking",
];

const VEHICLE_TYPES = ["2W", "3W", "4W"];

function PasswordStrength({ password }) {
  const score = [
    password.length >= 8,
    /[A-Z]/.test(password),
    /[0-9]/.test(password),
    /[^A-Za-z0-9]/.test(password),
  ].filter(Boolean).length;

  const colors = ["#FF3B2F", "#FF8C00", "#EAB308", "#22C55E"];
  const labels = ["Weak", "Fair", "Good", "Strong"];
  if (!password) return null;

  return (
    <div style={{ marginTop: "6px" }}>
      <div style={{ display: "flex", gap: "3px", marginBottom: "4px" }}>
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            style={{
              flex: 1,
              height: "3px",
              borderRadius: "2px",
              background: i < score ? colors[score - 1] : "rgba(255,255,255,0.10)",
              transition: "background 0.2s",
            }}
          />
        ))}
      </div>
      <p style={{ fontSize: "11px", color: score > 0 ? colors[score - 1] : "rgba(244,246,240,0.35)", margin: 0 }}>
        {score > 0 ? labels[score - 1] : ""}
      </p>
    </div>
  );
}

function StepIndicator({ current, total }) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "0", marginBottom: "32px" }}>
      {Array.from({ length: total }).map((_, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center" }}>
          <div
            style={{
              width: "28px",
              height: "28px",
              borderRadius: "50%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "12px",
              fontFamily: "JetBrains Mono, monospace",
              fontWeight: 700,
              background: i < current ? "#22C55E" : i === current ? "#C8FF00" : "transparent",
              border: i < current ? "none" : i === current ? "none" : "1.5px solid rgba(255,255,255,0.20)",
              color: i <= current ? "#080C0F" : "rgba(244,246,240,0.35)",
              transition: "all 0.2s",
              flexShrink: 0,
            }}
          >
            {i < current ? <Check style={{ width: "14px", height: "14px" }} /> : i + 1}
          </div>
          {i < total - 1 && (
            <div
              style={{
                width: "48px",
                height: "2px",
                background: i < current ? "#22C55E" : "rgba(255,255,255,0.10)",
                transition: "background 0.3s",
              }}
            />
          )}
        </div>
      ))}
    </div>
  );
}

export default function Register({ onLogin }) {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [showPw, setShowPw] = useState(false);

  const [form, setForm] = useState({
    garageName: "",
    city: "",
    phone: "",
    vehicleTypes: [],
    ownerName: "",
    email: "",
    password: "",
    agreed: false,
  });
  const [errors, setErrors] = useState({});

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const err = (k, msg) => setErrors((e) => ({ ...e, [k]: msg }));
  const clearErr = (k) => setErrors((e) => { const n = { ...e }; delete n[k]; return n; });

  const toggleVehicleType = (vt) => {
    const types = form.vehicleTypes.includes(vt)
      ? form.vehicleTypes.filter((t) => t !== vt)
      : [...form.vehicleTypes, vt];
    set("vehicleTypes", types);
  };

  const validateStep = (s) => {
    const newErrs = {};
    if (s === 0) {
      if (!form.garageName.trim()) newErrs.garageName = "Garage name is required";
      if (!form.city.trim()) newErrs.city = "City is required";
      if (!form.phone.trim()) newErrs.phone = "Phone number is required";
      if (form.vehicleTypes.length === 0) newErrs.vehicleTypes = "Select at least one vehicle type";
    } else if (s === 1) {
      if (!form.ownerName.trim()) newErrs.ownerName = "Your name is required";
      if (!form.email.trim() || !/\S+@\S+\.\S+/.test(form.email)) newErrs.email = "Valid email is required";
      if (form.password.length < 8) newErrs.password = "Password must be at least 8 characters";
    } else if (s === 2) {
      if (!form.agreed) newErrs.agreed = "You must accept the terms";
    }
    setErrors(newErrs);
    return Object.keys(newErrs).length === 0;
  };

  const next = () => {
    if (validateStep(step)) setStep((s) => s + 1);
  };

  const back = () => setStep((s) => s - 1);

  const submit = async () => {
    if (!validateStep(2)) return;
    setSubmitting(true);
    try {
      const res = await fetch(`${API}/organizations/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: form.garageName,
          city: form.city,
          phone: form.phone,
          vehicle_types: form.vehicleTypes,
          admin_name: form.ownerName,
          admin_email: form.email,
          admin_password: form.password,
          industry_type: "ev_garage",
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        if (data.detail?.includes("already registered") || data.detail?.includes("already exists")) {
          setErrors({ submit: "account_exists" });
        } else {
          setErrors({ submit: data.detail || "Something went wrong. Please try again or contact support@battwheels.com" });
        }
        return;
      }

      // Log in the new user
      const token = data.token;
      const org = data.organization;
      if (token && org && onLogin) {
        localStorage.setItem("token", token);
        localStorage.setItem("organization_id", org.organization_id);
        localStorage.setItem("organization", JSON.stringify(org));
        onLogin({ email: form.email, name: form.ownerName }, token, [org]);
      }
      toast.success(`Welcome to Battwheels OS, ${form.ownerName}!`);
      navigate("/dashboard");
    } catch {
      setErrors({ submit: "Something went wrong. Please try again or contact support@battwheels.com" });
    } finally {
      setSubmitting(false);
    }
  };

  const inputStyle = (hasErr) => ({
    width: "100%",
    padding: "12px 14px",
    background: "rgba(255,255,255,0.04)",
    border: `1px solid ${hasErr ? "#FF3B2F" : "rgba(255,255,255,0.12)"}`,
    borderRadius: "4px",
    color: "rgb(var(--bw-white))",
    fontSize: "14px",
    fontFamily: "Syne, sans-serif",
    outline: "none",
    boxSizing: "border-box",
  });

  const labelStyle = {
    display: "block",
    fontSize: "12px",
    fontFamily: "Syne, sans-serif",
    color: "rgb(var(--bw-white) / 0.55)",
    marginBottom: "6px",
    letterSpacing: "0.04em",
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        background: "rgb(var(--bw-black))",
        fontFamily: "Syne, sans-serif",
      }}
    >
      {/* ── LEFT PANEL ── */}
      <div
        className="hidden lg:flex"
        style={{
          width: "45%",
          flexDirection: "column",
          justifyContent: "center",
          padding: "60px 64px",
          background: "rgb(var(--bw-black))",
          borderRight: "1px solid rgba(255,255,255,0.06)",
          position: "relative",
          overflow: "hidden",
        }}
      >
        {/* Volt grid pattern */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            backgroundImage:
              "linear-gradient(rgba(200,255,0,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(200,255,0,0.04) 1px, transparent 1px)",
            backgroundSize: "40px 40px",
          }}
        />
        {/* Ambient glow */}
        <div
          style={{
            position: "absolute",
            bottom: "-100px",
            left: "-100px",
            width: "400px",
            height: "400px",
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(200,255,0,0.08) 0%, transparent 70%)",
            pointerEvents: "none",
          }}
        />

        <div style={{ position: "relative", zIndex: 1 }}>
          {/* Logo */}
          <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "56px" }}>
            <div
              style={{
                width: "36px",
                height: "36px",
                background: "rgb(var(--bw-volt))",
                borderRadius: "8px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Zap style={{ width: "20px", height: "20px", color: "rgb(var(--bw-black))" }} />
            </div>
            <span style={{ fontSize: "16px", fontWeight: 700, color: "rgb(var(--bw-white))", letterSpacing: "-0.01em" }}>
              Battwheels OS
            </span>
          </div>

          <p style={{ fontSize: "11px", color: "rgb(var(--bw-volt))", letterSpacing: "0.12em", marginBottom: "12px", fontFamily: "JetBrains Mono, monospace" }}>
            JOIN 1,000+ EV WORKSHOPS
          </p>
          <h1
            style={{
              fontSize: "36px",
              fontWeight: 800,
              color: "rgb(var(--bw-white))",
              lineHeight: 1.15,
              marginBottom: "12px",
            }}
          >
            Start your 14-day
            <br />
            <span style={{ color: "rgb(var(--bw-volt))" }}>free trial.</span>
          </h1>
          <p style={{ fontSize: "14px", color: "var(--bw-muted)", marginBottom: "40px" }}>
            No credit card required. Cancel anytime.
          </p>

          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {FEATURES.map((f) => (
              <div key={f} style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <div
                  style={{
                    width: "20px",
                    height: "20px",
                    borderRadius: "50%",
                    background: "rgba(200,255,0,0.12)",
                    border: "1px solid rgba(200,255,0,0.30)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                  }}
                >
                  <Check style={{ width: "11px", height: "11px", color: "rgb(var(--bw-volt))" }} />
                </div>
                <span style={{ fontSize: "14px", color: "rgba(244,246,240,0.70)" }}>{f}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── RIGHT PANEL: FORM ── */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "40px 24px",
          overflowY: "auto",
        }}
      >
        <div style={{ width: "100%", maxWidth: "420px" }}>
          <StepIndicator current={step} total={3} />

          {/* ── STEP 0: Garage Details ── */}
          {step === 0 && (
            <div>
              <h2 style={{ fontSize: "22px", fontWeight: 700, color: "rgb(var(--bw-white))", marginBottom: "4px" }}>
                Garage Details
              </h2>
              <p style={{ fontSize: "13px", color: "var(--bw-muted)", marginBottom: "28px" }}>
                Step 1 of 3 — Tell us about your workshop
              </p>

              <div style={{ marginBottom: "16px" }}>
                <label style={labelStyle}>Garage name *</label>
                <input
                  style={inputStyle(errors.garageName)}
                  placeholder="e.g. Kumar EV Service"
                  value={form.garageName}
                  onChange={(e) => { set("garageName", e.target.value); clearErr("garageName"); }}
                  data-testid="register-garage-name"
                />
                {errors.garageName && <p style={{ fontSize: "11px", color: "rgb(var(--bw-red))", marginTop: "4px" }}>{errors.garageName}</p>}
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "16px" }}>
                <div>
                  <label style={labelStyle}>City *</label>
                  <input
                    style={inputStyle(errors.city)}
                    placeholder="e.g. Mumbai"
                    value={form.city}
                    onChange={(e) => { set("city", e.target.value); clearErr("city"); }}
                    data-testid="register-city"
                  />
                  {errors.city && <p style={{ fontSize: "11px", color: "rgb(var(--bw-red))", marginTop: "4px" }}>{errors.city}</p>}
                </div>
                <div>
                  <label style={labelStyle}>Phone number *</label>
                  <input
                    style={inputStyle(errors.phone)}
                    placeholder="e.g. 9876543210"
                    value={form.phone}
                    onChange={(e) => { set("phone", e.target.value); clearErr("phone"); }}
                    data-testid="register-phone"
                  />
                  {errors.phone && <p style={{ fontSize: "11px", color: "rgb(var(--bw-red))", marginTop: "4px" }}>{errors.phone}</p>}
                </div>
              </div>

              <div style={{ marginBottom: "24px" }}>
                <label style={labelStyle}>Vehicle types serviced *</label>
                <div style={{ display: "flex", gap: "10px" }}>
                  {VEHICLE_TYPES.map((vt) => {
                    const sel = form.vehicleTypes.includes(vt);
                    return (
                      <button
                        key={vt}
                        onClick={() => { toggleVehicleType(vt); clearErr("vehicleTypes"); }}
                        data-testid={`register-vt-${vt}`}
                        style={{
                          flex: 1,
                          padding: "10px",
                          background: sel ? "rgba(200,255,0,0.12)" : "rgba(255,255,255,0.04)",
                          border: `1px solid ${sel ? "rgba(200,255,0,0.40)" : "rgba(255,255,255,0.12)"}`,
                          borderRadius: "4px",
                          color: sel ? "#C8FF00" : "rgba(244,246,240,0.55)",
                          fontSize: "13px",
                          fontWeight: sel ? 700 : 400,
                          cursor: "pointer",
                          transition: "all 0.15s",
                        }}
                      >
                        {vt}
                      </button>
                    );
                  })}
                </div>
                {errors.vehicleTypes && <p style={{ fontSize: "11px", color: "rgb(var(--bw-red))", marginTop: "4px" }}>{errors.vehicleTypes}</p>}
              </div>

              <button
                onClick={next}
                data-testid="register-step1-next"
                style={{
                  width: "100%",
                  padding: "14px",
                  background: "rgb(var(--bw-volt))",
                  border: "none",
                  borderRadius: "4px",
                  color: "rgb(var(--bw-black))",
                  fontSize: "14px",
                  fontWeight: 700,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "8px",
                }}
              >
                Next <ChevronRight style={{ width: "16px", height: "16px" }} />
              </button>
            </div>
          )}

          {/* ── STEP 1: Your Account ── */}
          {step === 1 && (
            <div>
              <h2 style={{ fontSize: "22px", fontWeight: 700, color: "rgb(var(--bw-white))", marginBottom: "4px" }}>
                Your Account
              </h2>
              <p style={{ fontSize: "13px", color: "var(--bw-muted)", marginBottom: "28px" }}>
                Step 2 of 3 — Create your login credentials
              </p>

              <div style={{ marginBottom: "16px" }}>
                <label style={labelStyle}>Your name *</label>
                <input
                  style={inputStyle(errors.ownerName)}
                  placeholder="e.g. Rajesh Kumar"
                  value={form.ownerName}
                  onChange={(e) => { set("ownerName", e.target.value); clearErr("ownerName"); }}
                  data-testid="register-owner-name"
                />
                {errors.ownerName && <p style={{ fontSize: "11px", color: "rgb(var(--bw-red))", marginTop: "4px" }}>{errors.ownerName}</p>}
              </div>

              <div style={{ marginBottom: "16px" }}>
                <label style={labelStyle}>Email address *</label>
                <input
                  type="email"
                  style={inputStyle(errors.email)}
                  placeholder="you@yourworkshop.com"
                  value={form.email}
                  onChange={(e) => { set("email", e.target.value); clearErr("email"); }}
                  data-testid="register-email"
                />
                {errors.email && <p style={{ fontSize: "11px", color: "rgb(var(--bw-red))", marginTop: "4px" }}>{errors.email}</p>}
              </div>

              <div style={{ marginBottom: "24px" }}>
                <label style={labelStyle}>Password * (min 8 characters)</label>
                <div style={{ position: "relative" }}>
                  <input
                    type={showPw ? "text" : "password"}
                    style={{ ...inputStyle(errors.password), paddingRight: "44px" }}
                    placeholder="Choose a strong password"
                    value={form.password}
                    onChange={(e) => { set("password", e.target.value); clearErr("password"); }}
                    data-testid="register-password"
                  />
                  <button
                    onClick={() => setShowPw(!showPw)}
                    style={{ position: "absolute", right: "12px", top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: "rgb(var(--bw-white) / 0.35)", padding: 0 }}
                  >
                    {showPw ? <EyeOff style={{ width: "16px", height: "16px" }} /> : <Eye style={{ width: "16px", height: "16px" }} />}
                  </button>
                </div>
                <PasswordStrength password={form.password} />
                {errors.password && <p style={{ fontSize: "11px", color: "rgb(var(--bw-red))", marginTop: "4px" }}>{errors.password}</p>}
              </div>

              <div style={{ display: "flex", gap: "10px" }}>
                <button
                  onClick={back}
                  style={{
                    flex: 1,
                    padding: "14px",
                    background: "transparent",
                    border: "1px solid rgba(255,255,255,0.12)",
                    borderRadius: "4px",
                    color: "rgba(244,246,240,0.60)",
                    fontSize: "14px",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "6px",
                  }}
                >
                  <ChevronLeft style={{ width: "16px", height: "16px" }} /> Back
                </button>
                <button
                  onClick={next}
                  data-testid="register-step2-next"
                  style={{
                    flex: 2,
                    padding: "14px",
                    background: "rgb(var(--bw-volt))",
                    border: "none",
                    borderRadius: "4px",
                    color: "rgb(var(--bw-black))",
                    fontSize: "14px",
                    fontWeight: 700,
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "8px",
                  }}
                >
                  Next <ChevronRight style={{ width: "16px", height: "16px" }} />
                </button>
              </div>
            </div>
          )}

          {/* ── STEP 2: Confirm ── */}
          {step === 2 && (
            <div>
              <h2 style={{ fontSize: "22px", fontWeight: 700, color: "rgb(var(--bw-white))", marginBottom: "4px" }}>
                Confirm & Launch
              </h2>
              <p style={{ fontSize: "13px", color: "var(--bw-muted)", marginBottom: "20px" }}>
                Step 3 of 3 — Review your details
              </p>

              {/* Summary card */}
              <div
                style={{
                  background: "rgb(255 255 255 / 0.03)",
                  border: "1px solid rgba(255,255,255,0.08)",
                  borderRadius: "4px",
                  padding: "16px",
                  marginBottom: "16px",
                }}
              >
                {[
                  ["Garage", form.garageName],
                  ["City", form.city],
                  ["Phone", form.phone],
                  ["Vehicle Types", form.vehicleTypes.join(", ")],
                  ["Name", form.ownerName],
                  ["Email", form.email],
                ].map(([label, value]) => (
                  <div key={label} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                    <span style={{ fontSize: "12px", color: "rgb(var(--bw-white) / 0.40)" }}>{label}</span>
                    <span style={{ fontSize: "12px", color: "rgb(var(--bw-white))", fontWeight: 500 }}>{value}</span>
                  </div>
                ))}
              </div>

              {/* Plan */}
              <div
                style={{
                  background: "rgba(200,255,0,0.05)",
                  border: "1px solid rgba(200,255,0,0.20)",
                  borderRadius: "4px",
                  padding: "12px 16px",
                  marginBottom: "16px",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <div>
                  <p style={{ fontSize: "13px", fontWeight: 700, color: "rgb(var(--bw-volt))", margin: 0 }}>14-day Free Trial</p>
                  <p style={{ fontSize: "11px", color: "rgb(var(--bw-white) / 0.40)", margin: "2px 0 0 0" }}>then ₹2,999/month. Cancel anytime.</p>
                </div>
                <Check style={{ width: "18px", height: "18px", color: "rgb(var(--bw-volt))" }} />
              </div>

              {/* Terms */}
              <div style={{ display: "flex", alignItems: "flex-start", gap: "10px", marginBottom: "20px" }}>
                <input
                  type="checkbox"
                  id="terms"
                  checked={form.agreed}
                  onChange={(e) => { set("agreed", e.target.checked); clearErr("agreed"); }}
                  data-testid="register-terms-checkbox"
                  style={{ marginTop: "2px", accentColor: "rgb(var(--bw-volt))", width: "16px", height: "16px", flexShrink: 0 }}
                />
                <label htmlFor="terms" style={{ fontSize: "12px", color: "rgb(var(--bw-white) / 0.55)", cursor: "pointer" }}>
                  I agree to the{" "}
                  <a href="#" style={{ color: "rgb(var(--bw-volt))", textDecoration: "none" }}>Terms of Service</a>{" "}
                  and{" "}
                  <a href="#" style={{ color: "rgb(var(--bw-volt))", textDecoration: "none" }}>Privacy Policy</a>
                </label>
              </div>
              {errors.agreed && <p style={{ fontSize: "11px", color: "rgb(var(--bw-red))", marginBottom: "12px" }}>{errors.agreed}</p>}

              {/* Error messages */}
              {errors.submit && errors.submit !== "account_exists" && (
                <div style={{ padding: "12px", background: "rgba(255,59,47,0.08)", border: "1px solid rgba(255,59,47,0.25)", borderRadius: "4px", marginBottom: "12px" }}>
                  <p style={{ fontSize: "12px", color: "rgb(var(--bw-red))", margin: 0 }}>{errors.submit}</p>
                </div>
              )}
              {errors.submit === "account_exists" && (
                <div style={{ padding: "12px", background: "rgba(234,179,8,0.08)", border: "1px solid rgba(234,179,8,0.25)", borderRadius: "4px", marginBottom: "12px" }}>
                  <p style={{ fontSize: "12px", color: "rgb(var(--bw-amber))", margin: 0 }}>
                    An account with this email exists.{" "}
                    <Link to="/login" style={{ color: "rgb(var(--bw-volt))" }}>Sign in →</Link>
                  </p>
                </div>
              )}

              <div style={{ display: "flex", gap: "10px" }}>
                <button
                  onClick={back}
                  style={{
                    flex: 1,
                    padding: "14px",
                    background: "transparent",
                    border: "1px solid rgba(255,255,255,0.12)",
                    borderRadius: "4px",
                    color: "rgba(244,246,240,0.60)",
                    fontSize: "14px",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "6px",
                  }}
                >
                  <ChevronLeft style={{ width: "16px", height: "16px" }} /> Back
                </button>
                <button
                  onClick={submit}
                  disabled={submitting}
                  data-testid="register-submit-btn"
                  style={{
                    flex: 2,
                    padding: "14px",
                    background: submitting ? "rgba(200,255,0,0.50)" : "#C8FF00",
                    border: "none",
                    borderRadius: "4px",
                    color: "rgb(var(--bw-black))",
                    fontSize: "14px",
                    fontWeight: 700,
                    cursor: submitting ? "not-allowed" : "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "8px",
                  }}
                >
                  {submitting ? "Creating account…" : "Create My Account →"}
                </button>
              </div>
            </div>
          )}

          <p style={{ textAlign: "center", marginTop: "20px", fontSize: "13px", color: "rgb(var(--bw-white) / 0.35)" }}>
            Already have an account?{" "}
            <Link to="/login" style={{ color: "rgb(var(--bw-volt))", textDecoration: "none" }}>
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
