/**
 * EstimateStatusBadge - Pure UI component for estimate status display
 * Props: { status: string }
 * No state, no API calls
 */

const statusConfig = {
  draft: {
    bg: "rgba(244,246,240,0.05)",
    text: "rgba(244,246,240,0.35)",
    border: "rgba(255,255,255,0.08)",
    label: "Draft"
  },
  sent: {
    bg: "rgba(59,158,255,0.10)",
    text: "rgb(var(--bw-blue))",
    border: "rgba(59,158,255,0.25)",
    label: "Sent"
  },
  customer_viewed: {
    bg: "rgba(26,255,228,0.10)",
    text: "rgb(var(--bw-teal))",
    border: "rgba(26,255,228,0.25)",
    label: "Viewed"
  },
  accepted: {
    bg: "rgba(34,197,94,0.10)",
    text: "rgb(var(--bw-green))",
    border: "rgba(34,197,94,0.25)",
    label: "Accepted"
  },
  declined: {
    bg: "rgba(255,59,47,0.10)",
    text: "rgb(var(--bw-red))",
    border: "rgba(255,59,47,0.25)",
    label: "Declined"
  },
  expired: {
    bg: "rgba(255,140,0,0.10)",
    text: "rgb(var(--bw-orange))",
    border: "rgba(255,140,0,0.25)",
    label: "Expired"
  },
  converted: {
    bg: "rgba(200,255,0,0.10)",
    text: "rgb(var(--bw-volt))",
    border: "rgba(200,255,0,0.25)",
    label: "Converted"
  },
  void: {
    bg: "rgba(244,246,240,0.05)",
    text: "rgba(244,246,240,0.25)",
    border: "rgba(255,255,255,0.08)",
    label: "Void"
  }
};

export function EstimateStatusBadge({ status }) {
  const config = statusConfig[status] || statusConfig.draft;
  
  return (
    <span
      data-testid={`status-badge-${status}`}
      style={{
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: "10px",
        fontWeight: 500,
        letterSpacing: "0.08em",
        textTransform: "uppercase",
        padding: "3px 10px",
        borderRadius: "2px",
        border: `1px solid ${config.border}`,
        display: "inline-flex",
        alignItems: "center",
        backgroundColor: config.bg,
        color: config.text
      }}
    >
      {config.label}
    </span>
  );
}

export default EstimateStatusBadge;
