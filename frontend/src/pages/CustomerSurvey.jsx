import { useState, useEffect, useCallback } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";

const API = process.env.REACT_APP_BACKEND_URL;

const RATING_LABELS = { 1: "Poor", 2: "Fair", 3: "Good", 4: "Very Good", 5: "Excellent" };

// ─── Star SVG ─────────────────────────────────────────────────────────────
function StarIcon({ filled, color }) {
  return (
    <svg viewBox="0 0 24 24" fill={filled ? color : "none"} stroke={color}
      strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round"
      style={{ width: 28, height: 28, display: "block" }}>
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────
const inject = (id, css) => {
  if (!document.getElementById(id)) {
    const s = document.createElement("style");
    s.id = id;
    s.textContent = css;
    document.head.appendChild(s);
  }
};

function useSurveyStyles() {
  useEffect(() => {
    const link = document.getElementById("bw-survey-font") || (() => {
      const l = document.createElement("link");
      l.id = "bw-survey-font";
      l.rel = "stylesheet";
      l.href = "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=DM+Serif+Display&family=Syne:wght@400;500;600;700&display=swap";
      document.head.appendChild(l);
      return l;
    })();
    inject("bw-survey-css", `
      @keyframes svFadeUp {
        from { opacity:0; transform:translateY(20px); }
        to   { opacity:1; transform:translateY(0); }
      }
      @keyframes svCheckIn {
        0%   { transform:scale(0.5) rotate(-20deg); opacity:0; }
        70%  { transform:scale(1.1) rotate(3deg); }
        100% { transform:scale(1) rotate(0deg); opacity:1; }
      }
      @keyframes svSpin {
        to { transform:rotate(360deg); }
      }
      .sv-page * { box-sizing:border-box; }
      .sv-page {
        min-height:100vh;
        background:#080C0F;
        display:flex; align-items:flex-start; justify-content:center;
        padding:48px 16px 64px;
        position:relative; overflow:hidden;
        font-family:'Syne',sans-serif;
      }
      .sv-grid {
        position:absolute; inset:0; pointer-events:none;
        background-image:
          linear-gradient(rgba(200,255,0,0.03) 1px, transparent 1px),
          linear-gradient(90deg, rgba(200,255,0,0.03) 1px, transparent 1px);
        background-size:40px 40px;
      }
      .sv-card {
        position:relative; z-index:1;
        width:100%; max-width:480px;
        animation:svFadeUp 0.5s ease forwards;
      }
      .sv-brand {
        text-align:center; margin-bottom:32px;
      }
      .sv-brand-logo {
        width:48px; height:48px; border-radius:8px;
        object-fit:cover; margin-bottom:12px;
        border:1px solid rgba(255,255,255,0.10);
      }
      .sv-brand-name {
        font-family:'Syne',sans-serif; font-size:20px; font-weight:600;
        color:#F4F6F0; margin:0 0 4px;
      }
      .sv-brand-sub {
        font-family:'JetBrains Mono',monospace;
        font-size:11px; color:rgba(244,246,240,0.35);
        letter-spacing:0.12em; text-transform:uppercase; margin:0;
      }
      .sv-vehicle-card {
        background:rgba(255,255,255,0.04);
        border:1px solid rgba(255,255,255,0.07);
        border-radius:4px; padding:16px 20px;
        margin:0 0 28px;
      }
      .sv-vehicle-name {
        font-family:'Syne',sans-serif; font-size:16px; font-weight:600;
        color:#F4F6F0; margin:0 0 4px;
      }
      .sv-vehicle-title {
        font-size:13px; color:rgba(244,246,240,0.45); margin:0 0 8px;
      }
      .sv-vehicle-date {
        font-family:'JetBrains Mono',monospace; font-size:11px;
        color:rgba(244,246,240,0.25); margin:0;
      }
      .sv-rating-label-text {
        font-size:14px; color:rgba(244,246,240,0.50);
        margin:0 0 16px; font-family:'Syne',sans-serif;
      }
      .sv-stars {
        display:flex; gap:8px; margin-bottom:8px;
      }
      .sv-star-btn {
        background:none; border:none; cursor:pointer;
        padding:8px; border-radius:4px;
        transition:transform 0.08s ease;
        display:flex; align-items:center; justify-content:center;
      }
      .sv-star-btn:hover { transform:scale(1.15); }
      .sv-star-btn:active { transform:scale(0.95); }
      .sv-rating-word {
        font-family:'JetBrains Mono',monospace; font-size:11px;
        color:#C8FF00; letter-spacing:0.08em; min-height:16px;
        transition:opacity 0.15s ease;
      }
      .sv-section-label {
        font-family:'JetBrains Mono',monospace; font-size:10px;
        color:rgba(244,246,240,0.30); letter-spacing:0.12em;
        text-transform:uppercase; margin:0 0 8px;
      }
      .sv-textarea {
        width:100%; min-height:96px;
        background:rgba(255,255,255,0.04);
        border:1px solid rgba(255,255,255,0.10);
        border-radius:4px; padding:12px 14px;
        font-family:'Syne',sans-serif; font-size:14px; color:#F4F6F0;
        resize:vertical; outline:none;
        transition:border-color 0.15s ease;
        line-height:1.5;
      }
      .sv-textarea::placeholder { color:rgba(244,246,240,0.25); }
      .sv-textarea:focus { border-color:rgba(200,255,0,0.50); }
      .sv-recommend-label {
        font-size:14px; color:rgba(244,246,240,0.50); margin:0 0 12px;
      }
      .sv-recommend-btns {
        display:flex; gap:10px;
      }
      .sv-recommend-btn {
        flex:1; padding:10px 0; border-radius:4px; cursor:pointer;
        font-family:'Syne',sans-serif; font-size:13px; font-weight:500;
        transition:all 0.15s ease; border:1px solid rgba(255,255,255,0.12);
        background:transparent; color:rgba(244,246,240,0.50);
      }
      .sv-recommend-btn.yes.active {
        background:rgba(34,197,94,0.10);
        border-color:rgba(34,197,94,0.30); color:#22C55E;
      }
      .sv-recommend-btn.no.active {
        background:rgba(255,59,47,0.08);
        border-color:rgba(255,59,47,0.25); color:#FF3B2F;
      }
      .sv-submit-btn {
        width:100%; height:44px; border-radius:4px; border:none;
        font-family:'JetBrains Mono',monospace; font-size:13px;
        font-weight:700; letter-spacing:0.08em; text-transform:uppercase;
        cursor:pointer; transition:all 0.15s ease; margin-top:28px;
        display:flex; align-items:center; justify-content:center; gap:8px;
      }
      .sv-submit-btn.disabled {
        background:rgba(200,255,0,0.20); color:rgba(8,12,15,0.40);
        cursor:not-allowed;
      }
      .sv-submit-btn.enabled {
        background:#C8FF00; color:#080C0F;
      }
      .sv-submit-btn.enabled:hover {
        transform:translateY(-1px);
        box-shadow:0 4px 20px rgba(200,255,0,0.20);
      }
      .sv-submit-btn.loading {
        background:rgba(200,255,0,0.60); color:#080C0F; cursor:not-allowed;
      }
      .sv-spinner {
        width:16px; height:16px; border-radius:50%;
        border:2px solid rgba(8,12,15,0.30);
        border-top-color:#080C0F;
        animation:svSpin 0.7s linear infinite;
        flex-shrink:0;
      }
      .sv-divider {
        height:1px; background:rgba(255,255,255,0.07); margin:28px 0;
      }
      .sv-thanks {
        text-align:center; padding:24px 0;
        animation:svFadeUp 0.4s ease forwards;
      }
      .sv-thanks-circle {
        width:56px; height:56px; border-radius:50%;
        background:rgba(34,197,94,0.12);
        border:1px solid rgba(34,197,94,0.30);
        display:flex; align-items:center; justify-content:center;
        margin:0 auto 20px;
        animation:svCheckIn 0.5s 0.1s ease both;
      }
      .sv-thanks-title {
        font-family:'DM Serif Display',serif; font-size:32px;
        color:#F4F6F0; margin:0 0 10px;
      }
      .sv-thanks-body {
        font-size:14px; color:rgba(244,246,240,0.50);
        max-width:280px; margin:0 auto 24px; line-height:1.6;
      }
      .sv-maps-btn {
        display:inline-flex; align-items:center; gap:6px;
        padding:10px 20px; border-radius:4px;
        border:1px solid rgba(255,255,255,0.15);
        background:transparent; color:rgba(244,246,240,0.60);
        font-family:'Syne',sans-serif; font-size:13px;
        cursor:pointer; text-decoration:none;
        transition:all 0.15s ease;
      }
      .sv-maps-btn:hover {
        border-color:rgba(200,255,0,0.40); color:#C8FF00;
      }
      .sv-error-state {
        text-align:center; padding:40px 20px;
      }
      .sv-error-icon {
        font-size:40px; margin-bottom:16px; opacity:0.5;
      }
      .sv-error-title {
        font-size:20px; font-weight:600; color:#F4F6F0; margin:0 0 8px;
      }
      .sv-error-body {
        font-size:14px; color:rgba(244,246,240,0.40); margin:0;
        line-height:1.6;
      }
      .sv-skeleton {
        background:rgba(255,255,255,0.06); border-radius:4px;
        animation:svPulse 1.5s ease-in-out infinite;
      }
      @keyframes svPulse {
        0%, 100% { opacity:1; } 50% { opacity:0.4; }
      }
    `);
  }, []);
}

// ─── Skeleton Loading ─────────────────────────────────────────────────────
function SkeletonForm() {
  return (
    <div>
      <div className="sv-brand">
        <div className="sv-skeleton" style={{ width: 48, height: 48, borderRadius: 8, margin: "0 auto 12px" }} />
        <div className="sv-skeleton" style={{ width: 140, height: 20, margin: "0 auto 6px" }} />
        <div className="sv-skeleton" style={{ width: 180, height: 12, margin: "0 auto" }} />
      </div>
      <div className="sv-vehicle-card">
        <div className="sv-skeleton" style={{ width: "60%", height: 20, marginBottom: 8 }} />
        <div className="sv-skeleton" style={{ width: "80%", height: 14, marginBottom: 8 }} />
        <div className="sv-skeleton" style={{ width: "40%", height: 12 }} />
      </div>
      <div className="sv-skeleton" style={{ width: "50%", height: 14, marginBottom: 16 }} />
      <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
        {[1,2,3,4,5].map(i => <div key={i} className="sv-skeleton" style={{ width: 44, height: 44, borderRadius: 4 }} />)}
      </div>
      <div className="sv-skeleton" style={{ width: "100%", height: 96, marginBottom: 20 }} />
      <div className="sv-skeleton" style={{ width: "100%", height: 44 }} />
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────
export default function CustomerSurvey() {
  useSurveyStyles();
  const { token } = useParams();

  const [state, setState] = useState("loading"); // loading | form | thanks | error | submitted
  const [errorMsg, setErrorMsg] = useState("");
  const [surveyData, setSurveyData] = useState(null);
  const [rating, setRating] = useState(0);
  const [hovered, setHovered] = useState(0);
  const [feedback, setFeedback] = useState("");
  const [recommend, setRecommend] = useState(null); // true | false | null
  const [submitting, setSubmitting] = useState(false);

  // ── Fetch survey metadata ─────────────────────────────────────────────
  useEffect(() => {
    if (!token) { setState("error"); setErrorMsg("Invalid survey link."); return; }
    axios.get(`${API}/api/public/survey/${token}`)
      .then(r => { setSurveyData(r.data); setState("form"); })
      .catch(err => {
        const status = err?.response?.status;
        if (status === 404) { setState("error"); setErrorMsg("Survey not found or expired."); }
        else if (status === 409) { setState("submitted"); }
        else { setState("error"); setErrorMsg("Unable to load survey. Please try again."); }
      });
  }, [token]);

  // ── Submit ─────────────────────────────────────────────────────────────
  const handleSubmit = useCallback(async () => {
    if (!rating || submitting) return;
    setSubmitting(true);
    try {
      await axios.post(`${API}/api/public/survey/${token}`, {
        rating, feedback, would_recommend: recommend,
      });
      setState("thanks");
    } catch (err) {
      const status = err?.response?.status;
      if (status === 400 && err?.response?.data?.detail?.includes("already")) {
        setState("submitted");
      } else {
        setErrorMsg("Submission failed. Please try again.");
        setState("error");
      }
    } finally {
      setSubmitting(false);
    }
  }, [rating, feedback, recommend, token, submitting]);

  // ── Effective star display ─────────────────────────────────────────────
  const effectiveRating = hovered || rating;

  const VOLT = "#C8FF00";
  const VOLT_DIM = "rgba(200,255,0,0.20)";
  const VOLT_MID = "rgba(200,255,0,0.55)";

  function starColor(idx) {
    if (hovered > 0) return idx <= hovered ? VOLT_MID : VOLT_DIM;
    return idx <= rating ? VOLT : VOLT_DIM;
  }

  return (
    <div className="sv-page">
      <div className="sv-grid" />
      <div className="sv-card" data-testid="survey-page">

        {/* ── LOADING ────────────────────────────────────────────── */}
        {state === "loading" && <SkeletonForm />}

        {/* ── ERROR ──────────────────────────────────────────────── */}
        {state === "error" && (
          <div className="sv-error-state" data-testid="survey-error">
            <div className="sv-error-icon">⚠</div>
            <p className="sv-error-title">Survey not available</p>
            <p className="sv-error-body">
              {errorMsg || "This survey link has expired or has already been submitted."}
            </p>
          </div>
        )}

        {/* ── ALREADY SUBMITTED ───────────────────────────────────── */}
        {state === "submitted" && (
          <div className="sv-error-state" data-testid="survey-already-submitted">
            <div className="sv-error-icon" style={{ opacity: 1 }}>✓</div>
            <p className="sv-error-title" style={{ color: "rgb(var(--bw-volt))" }}>Already received</p>
            <p className="sv-error-body">
              You have already submitted a review for this service. Thank you!
            </p>
          </div>
        )}

        {/* ── THANK YOU STATE ─────────────────────────────────────── */}
        {state === "thanks" && surveyData && (
          <div className="sv-thanks" data-testid="survey-thanks">
            <div className="sv-thanks-circle">
              <svg viewBox="0 0 24 24" fill="none" stroke="#22C55E" strokeWidth={2.5}
                strokeLinecap="round" strokeLinejoin="round" style={{ width: 28, height: 28 }}>
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <h2 className="sv-thanks-title">Thank you!</h2>
            <p className="sv-thanks-body">
              Your feedback helps{" "}
              <span style={{ color: "rgb(var(--bw-white))", fontWeight: 600 }}>
                {surveyData.org_name}
              </span>{" "}
              serve you better.
            </p>
            {surveyData.google_maps_url && (
              <>
                <div className="sv-divider" />
                <p style={{ fontSize: 13, color: "rgba(244,246,240,0.40)", marginBottom: 12, fontFamily: "Syne" }}>
                  Enjoyed the service?
                </p>
                <a
                  href={surveyData.google_maps_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="sv-maps-btn"
                  data-testid="survey-google-maps-btn"
                >
                  Leave a Google Review →
                </a>
              </>
            )}
          </div>
        )}

        {/* ── FORM ────────────────────────────────────────────────── */}
        {state === "form" && surveyData && (
          <>
            {/* Brand identity */}
            <div className="sv-brand" data-testid="survey-brand">
              {surveyData.org_logo_url ? (
                <img src={surveyData.org_logo_url} alt={surveyData.org_name}
                  className="sv-brand-logo" />
              ) : (
                <div style={{
                  width: 48, height: 48, borderRadius: 8, margin: "0 auto 12px",
                  background: "rgba(200,255,0,0.12)", border: "1px solid rgba(200,255,0,0.25)",
                  display: "flex", alignItems: "center", justifyContent: "center"
                }}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="#C8FF00" strokeWidth={1.5}
                    style={{ width: 22, height: 22 }}>
                    <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
                    <polyline points="9 22 9 12 15 12 15 22" />
                  </svg>
                </div>
              )}
              <p className="sv-brand-name">{surveyData.org_name}</p>
              <p className="sv-brand-sub">How was your service?</p>
            </div>

            {/* Vehicle card */}
            <div className="sv-vehicle-card" data-testid="survey-vehicle-card">
              <p className="sv-vehicle-name">
                {surveyData.vehicle_make && surveyData.vehicle_model
                  ? `${surveyData.vehicle_make} ${surveyData.vehicle_model}`
                  : surveyData.ticket_title || "Your Vehicle"}
              </p>
              <p className="sv-vehicle-title">{surveyData.ticket_title}</p>
              {surveyData.completed_date && (
                <p className="sv-vehicle-date">Serviced on {surveyData.completed_date}</p>
              )}
            </div>

            {/* Rating */}
            <div style={{ marginBottom: 24 }}>
              <p className="sv-rating-label-text">Rate your experience</p>
              <div className="sv-stars" data-testid="survey-stars">
                {[1, 2, 3, 4, 5].map(idx => (
                  <button
                    key={idx}
                    className="sv-star-btn"
                    data-testid={`survey-star-${idx}`}
                    aria-label={`Rate ${idx} star${idx > 1 ? "s" : ""}`}
                    onMouseEnter={() => setHovered(idx)}
                    onMouseLeave={() => setHovered(0)}
                    onClick={() => setRating(prev => prev === idx ? 0 : idx)}
                  >
                    <StarIcon
                      filled={idx <= effectiveRating}
                      color={starColor(idx)}
                    />
                  </button>
                ))}
              </div>
              <p className="sv-rating-word" data-testid="survey-rating-label"
                style={{ opacity: effectiveRating ? 1 : 0 }}>
                {RATING_LABELS[effectiveRating] || ""}
              </p>
            </div>

            {/* Review text */}
            <div style={{ marginTop: 24 }}>
              <p className="sv-section-label">Tell us more (optional)</p>
              <textarea
                className="sv-textarea"
                data-testid="survey-feedback-textarea"
                placeholder={"What went well?\nWhat could be better?"}
                value={feedback}
                onChange={e => setFeedback(e.target.value)}
                maxLength={1000}
              />
            </div>

            {/* Recommend */}
            <div style={{ marginTop: 20 }}>
              <p className="sv-recommend-label">Would you recommend us?</p>
              <div className="sv-recommend-btns">
                <button
                  className={`sv-recommend-btn yes${recommend === true ? " active" : ""}`}
                  data-testid="survey-recommend-yes"
                  onClick={() => setRecommend(prev => prev === true ? null : true)}
                >
                  👍 Yes, definitely
                </button>
                <button
                  className={`sv-recommend-btn no${recommend === false ? " active" : ""}`}
                  data-testid="survey-recommend-no"
                  onClick={() => setRecommend(prev => prev === false ? null : false)}
                >
                  Not really
                </button>
              </div>
            </div>

            {/* Submit */}
            <button
              className={`sv-submit-btn ${submitting ? "loading" : rating ? "enabled" : "disabled"}`}
              data-testid="survey-submit-btn"
              onClick={handleSubmit}
              disabled={!rating || submitting}
              aria-disabled={!rating || submitting}
            >
              {submitting ? (
                <><div className="sv-spinner" /> Submitting...</>
              ) : (
                "Submit Review"
              )}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
