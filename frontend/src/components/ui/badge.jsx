import * as React from "react"
import { cva } from "class-variance-authority";

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded border px-2.5 py-0.5 text-[10px] font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 font-mono tracking-[0.08em] uppercase",
  {
    variants: {
      variant: {
        default:
          "border-[rgba(200,255,0,0.25)] bg-[rgba(200,255,0,0.10)] text-[#C8FF00]",
        secondary:
          "border-[rgba(255,255,255,0.08)] bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)]",
        destructive:
          "border-[rgba(255,59,47,0.25)] bg-[rgba(255,59,47,0.10)] text-[#FF3B2F]",
        outline: 
          "border-[rgba(255,255,255,0.13)] text-[rgba(244,246,240,0.7)]",
        // Status variants
        open:
          "border-[rgba(200,255,0,0.25)] bg-[rgba(200,255,0,0.10)] text-[#C8FF00]",
        new:
          "border-[rgba(200,255,0,0.25)] bg-[rgba(200,255,0,0.10)] text-[#C8FF00]",
        "in-progress":
          "border-[rgba(255,140,0,0.25)] bg-[rgba(255,140,0,0.10)] text-[#FF8C00]",
        active:
          "border-[rgba(255,140,0,0.25)] bg-[rgba(255,140,0,0.10)] text-[#FF8C00]",
        assigned:
          "border-[rgba(59,158,255,0.25)] bg-[rgba(59,158,255,0.10)] text-[#3B9EFF]",
        approved:
          "border-[rgba(34,197,94,0.25)] bg-[rgba(34,197,94,0.10)] text-[#22C55E]",
        closed:
          "border-[rgba(255,255,255,0.08)] bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)]",
        resolved:
          "border-[rgba(255,255,255,0.08)] bg-[rgba(244,246,240,0.05)] text-[rgba(244,246,240,0.35)]",
        escalated:
          "border-[rgba(255,59,47,0.25)] bg-[rgba(255,59,47,0.10)] text-[#FF3B2F]",
        critical:
          "border-[rgba(255,59,47,0.25)] bg-[rgba(255,59,47,0.10)] text-[#FF3B2F]",
        // Priority variants
        high:
          "border-[rgba(255,59,47,0.20)] bg-[rgba(255,59,47,0.10)] text-[#FF3B2F]",
        medium:
          "border-[rgba(234,179,8,0.20)] bg-[rgba(234,179,8,0.10)] text-[#EAB308]",
        low:
          "border-[rgba(34,197,94,0.20)] bg-[rgba(34,197,94,0.10)] text-[#22C55E]",
        // General semantic variants
        success:
          "border-[rgba(34,197,94,0.25)] bg-[rgba(34,197,94,0.10)] text-[#22C55E]",
        warning:
          "border-[rgba(234,179,8,0.25)] bg-[rgba(234,179,8,0.10)] text-[#EAB308]",
        info:
          "border-[rgba(59,158,255,0.25)] bg-[rgba(59,158,255,0.10)] text-[#3B9EFF]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Badge({
  className,
  variant,
  ...props
}) {
  return (<div className={cn(badgeVariants({ variant }), className)} {...props} />);
}

export { Badge, badgeVariants }
