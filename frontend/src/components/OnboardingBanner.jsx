import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { User, Car, Wrench, Package, FileText, Users, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";
import { API, getAuthHeaders } from "@/App";

const STEPS = [
  {
    key: "add_first_contact",
    title: "Add your first customer",
    sub: "Create a contact record",
    Icon: User,
    href: "/contacts",
  },
  {
    key: "add_first_vehicle",
    title: "Register a vehicle",
    sub: "Link a vehicle to a customer",
    Icon: Car,
    href: "/contacts",
  },
  {
    key: "create_first_ticket",
    title: "Create a service ticket",
    sub: "Start your first repair job",
    Icon: Wrench,
    href: "/tickets/new",
  },
  {
    key: "add_inventory_item",
    title: "Add inventory items",
    sub: "Set up your parts catalogue",
    Icon: Package,
    href: "/items",
  },
  {
    key: "create_first_invoice",
    title: "Send your first invoice",
    sub: "Bill a customer for service",
    Icon: FileText,
    href: "/invoices",
  },
  {
    key: "invite_team_member",
    title: "Invite a team member",
    sub: "Add a technician or manager",
    Icon: Users,
    href: "/team",
  },
];

export function OnboardingBanner() {
  const navigate = useNavigate();
  const [status, setStatus] = useState(null);
  const [celebrating, setCelebrating] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API}/organizations/onboarding/status`, {
        headers: getAuthHeaders(),
        credentials: "include",
      });
      if (!res.ok) return;
      const data = await res.json();

      // Detect newly completed steps and show toasts
      const prevKey = "onboarding_steps_seen";
      const prevSteps = JSON.parse(localStorage.getItem(prevKey) || "[]");
      const newSteps = data.onboarding_steps_completed || [];
      const justCompleted = newSteps.filter((s) => !prevSteps.includes(s));

      if (justCompleted.length > 0 && prevSteps.length > 0) {
        justCompleted.forEach((stepKey) => {
          const stepInfo = STEPS.find((s) => s.key === stepKey);
          if (stepInfo) {
            toast.success(`Step complete: ${stepInfo.title}`, {
              description: "Keep going! You're making great progress.",
            });
          }
        });
      }
      localStorage.setItem(prevKey, JSON.stringify(newSteps));

      // Trigger celebration if all steps just reached
      if (
        data.completed_count >= data.total_steps &&
        !data.onboarding_completed &&
        !celebrating
      ) {
        setCelebrating(true);
        setTimeout(() => {
          setDismissed(true);
          setCelebrating(false);
        }, 5000);
      }

      setStatus(data);
    } catch (e) {
      // Silently ignore
    }
  }, [celebrating]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const skipOnboarding = async () => {
    try {
      await fetch(`${API}/organizations/onboarding/skip`, {
        method: "POST",
        headers: getAuthHeaders(),
        credentials: "include",
      });
      toast.info("You can always find setup tips in Settings");
      setDismissed(true);
    } catch (e) {
      // ignore
    }
  };

  if (dismissed) return null;
  if (!status) return null;
  if (!status.show_onboarding) return null;
  if (status.onboarding_completed && !celebrating) return null;

  const completedSteps = status.onboarding_steps_completed || [];
  const completedCount = completedSteps.length;
  const totalSteps = status.total_steps || 6;
  const progressPercent = Math.round((completedCount / totalSteps) * 100);

  // Celebration banner
  if (celebrating || completedCount >= totalSteps) {
    return (
      <div
        data-testid="onboarding-celebration"
        style={{
          background: "rgba(34,197,94,0.08)",
          border: "1px solid rgba(34,197,94,0.20)",
          borderRadius: "4px",
          padding: "20px 24px",
          marginBottom: "24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div>
          <p
            style={{
              fontFamily: "Syne, sans-serif",
              fontSize: "16px",
              color: "rgb(var(--bw-white))",
              fontWeight: 600,
              margin: 0,
            }}
          >
            You're all set!
          </p>
          <p
            style={{
              fontFamily: "Syne, sans-serif",
              fontSize: "13px",
              color: "rgba(244,246,240,0.55)",
              marginTop: "4px",
              marginBottom: 0,
            }}
          >
            Your workshop is fully configured.
          </p>
        </div>
        <CheckCircle2 style={{ width: "32px", height: "32px", color: "rgb(var(--bw-green))", flexShrink: 0 }} />
      </div>
    );
  }

  return (
    <div
      data-testid="onboarding-banner"
      style={{
        background: "rgba(200,255,0,0.05)",
        border: "1px solid rgba(200,255,0,0.15)",
        borderRadius: "4px",
        padding: "20px 24px",
        marginBottom: "24px",
      }}
    >
      {/* Header row */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "10px",
        }}
      >
        <p
          style={{
            fontFamily: "Syne, sans-serif",
            fontSize: "16px",
            color: "rgb(var(--bw-white))",
            fontWeight: 600,
            margin: 0,
          }}
        >
          Get started with Battwheels OS
        </p>
        <p
          data-testid="onboarding-progress-text"
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: "12px",
            color: "rgb(var(--bw-volt))",
            margin: 0,
          }}
        >
          {completedCount} of {totalSteps} complete
        </p>
      </div>

      {/* Progress bar */}
      <div
        style={{
          width: "100%",
          height: "3px",
          background: "rgba(255,255,255,0.08)",
          borderRadius: "2px",
          marginBottom: "16px",
        }}
      >
        <div
          data-testid="onboarding-progress-bar"
          style={{
            height: "3px",
            width: `${progressPercent}%`,
            background: "rgb(var(--bw-volt))",
            borderRadius: "2px",
            transition: "width 0.5s ease",
          }}
        />
      </div>

      {/* Steps grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(2, 1fr)",
          gap: "8px",
        }}
        className="onboarding-steps-grid"
      >
        {STEPS.map((step) => {
          const isComplete = completedSteps.includes(step.key);
          const { Icon } = step;

          return (
            <div
              key={step.key}
              data-testid={`onboarding-step-${step.key}`}
              onClick={() => navigate(step.href)}
              style={{
                background: isComplete
                  ? "rgba(34,197,94,0.04)"
                  : "rgba(255,255,255,0.03)",
                border: isComplete
                  ? "1px solid rgba(34,197,94,0.15)"
                  : "1px solid rgba(255,255,255,0.07)",
                borderRadius: "4px",
                padding: "14px 16px",
                display: "flex",
                alignItems: "center",
                gap: "12px",
                cursor: "pointer",
                transition: "border-color 0.15s ease, background 0.15s ease",
              }}
            >
              {/* Completion circle */}
              <div
                style={{
                  width: "20px",
                  height: "20px",
                  borderRadius: "50%",
                  flexShrink: 0,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  background: isComplete ? "#22C55E" : "transparent",
                  border: isComplete ? "none" : "1.5px solid rgba(255,255,255,0.20)",
                }}
              >
                {isComplete && (
                  <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                    <path
                      d="M1 4l2.5 2.5L9 1"
                      stroke="white"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                )}
              </div>

              {/* Text */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <p
                  style={{
                    fontFamily: "Syne, sans-serif",
                    fontSize: "14px",
                    color: isComplete ? "rgba(244,246,240,0.40)" : "#F4F6F0",
                    textDecoration: isComplete ? "line-through" : "none",
                    margin: 0,
                    fontWeight: 500,
                  }}
                >
                  {step.title}
                </p>
                <p
                  style={{
                    fontFamily: "Syne, sans-serif",
                    fontSize: "12px",
                    color: "rgba(244,246,240,0.35)",
                    margin: "2px 0 0 0",
                  }}
                >
                  {step.sub}
                </p>
              </div>

              {/* Icon */}
              <Icon
                style={{
                  width: "16px",
                  height: "16px",
                  color: isComplete
                    ? "rgba(34,197,94,0.5)"
                    : "rgba(244,246,240,0.30)",
                  flexShrink: 0,
                }}
              />
            </div>
          );
        })}
      </div>

      {/* Footer: Skip setup */}
      <div
        style={{
          display: "flex",
          justifyContent: "flex-end",
          marginTop: "14px",
        }}
      >
        <button
          data-testid="onboarding-skip-btn"
          onClick={skipOnboarding}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            color: "rgba(244,246,240,0.35)",
            fontFamily: "Syne, sans-serif",
            fontSize: "12px",
            padding: 0,
          }}
        >
          Skip setup
        </button>
      </div>
    </div>
  );
}
