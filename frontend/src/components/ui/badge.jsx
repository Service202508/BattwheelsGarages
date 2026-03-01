import * as React from "react"
import { cva } from "class-variance-authority";

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded border px-2.5 py-0.5 text-[10px] font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 font-mono tracking-[0.08em] uppercase",
  {
    variants: {
      variant: {
        default:
          "border-bw-volt/25 bg-bw-volt/10 text-bw-volt",
        secondary:
          "border-white/[0.08] bg-bw-white/5 text-bw-white/35",
        destructive:
          "border-bw-red/25 bg-bw-red/10 text-bw-red",
        outline: 
          "border-white/[0.13] text-bw-white/70",
        // Status variants
        open:
          "border-bw-volt/25 bg-bw-volt/10 text-bw-volt",
        new:
          "border-bw-volt/25 bg-bw-volt/10 text-bw-volt",
        "in-progress":
          "border-bw-orange/25 bg-bw-orange/10 text-bw-orange",
        active:
          "border-bw-orange/25 bg-bw-orange/10 text-bw-orange",
        assigned:
          "border-bw-blue/25 bg-bw-blue/10 text-bw-blue",
        approved:
          "border-bw-green/25 bg-bw-green/10 text-bw-green",
        closed:
          "border-white/[0.08] bg-bw-white/5 text-bw-white/35",
        resolved:
          "border-white/[0.08] bg-bw-white/5 text-bw-white/35",
        escalated:
          "border-bw-red/25 bg-bw-red/10 text-bw-red",
        critical:
          "border-bw-red/25 bg-bw-red/10 text-bw-red",
        // Priority variants
        high:
          "border-bw-red/20 bg-bw-red/10 text-bw-red",
        medium:
          "border-bw-amber/20 bg-bw-amber/10 text-bw-amber",
        low:
          "border-bw-green/20 bg-bw-green/10 text-bw-green",
        // General semantic variants
        success:
          "border-bw-green/25 bg-bw-green/10 text-bw-green",
        warning:
          "border-bw-amber/25 bg-bw-amber/10 text-bw-amber",
        info:
          "border-bw-blue/25 bg-bw-blue/10 text-bw-blue",
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
