import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";
import * as Sentry from "@sentry/react";

const SENTRY_DSN = process.env.REACT_APP_SENTRY_DSN || "";

if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration({
        maskAllText: true,
        blockAllMedia: true,
      }),
    ],
    tracesSampleRate: 0.1,
    replaysSessionSampleRate: 0.05,
    replaysOnErrorSampleRate: 1.0,
    environment: process.env.NODE_ENV || "development",
  });
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <Sentry.ErrorBoundary
      fallback={
        <div style={{
          display: "flex", flexDirection: "column", alignItems: "center",
          justifyContent: "center", height: "100vh", background: "#080C0F", color: "#F4F6F0"
        }}>
          <h2 style={{ fontSize: "20px", marginBottom: "8px" }}>Something went wrong</h2>
          <p style={{ color: "rgba(244,246,240,0.45)", marginBottom: "16px" }}>
            Our team has been notified. Please refresh the page.
          </p>
          <button
            onClick={() => window.location.reload()}
            style={{
              background: "#C8FF00", color: "#080C0F", border: "none",
              padding: "8px 20px", borderRadius: "6px", cursor: "pointer", fontWeight: "bold"
            }}
          >
            Refresh
          </button>
        </div>
      }
    >
      <App />
    </Sentry.ErrorBoundary>
  </React.StrictMode>,
);
