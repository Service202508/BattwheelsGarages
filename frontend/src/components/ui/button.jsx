import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva } from "class-variance-authority";

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[rgba(200,255,0,0.3)] disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "bg-[#C8FF00] text-[#080C0F] font-bold hover:bg-[#d4ff1a] hover:shadow-[0_0_20px_rgba(200,255,0,0.3)]",
        destructive:
          "bg-[rgba(255,59,47,0.1)] text-[#FF3B2F] border border-[rgba(255,59,47,0.2)] hover:bg-[rgba(255,59,47,0.15)]",
        outline:
          "border border-[rgba(255,255,255,0.13)] text-[rgba(244,246,240,0.7)] hover:border-[rgba(200,255,0,0.3)] hover:text-[#F4F6F0]",
        secondary:
          "bg-[#111820] text-[rgba(244,246,240,0.7)] border border-[rgba(255,255,255,0.07)] hover:bg-[rgba(200,255,0,0.06)] hover:text-[#F4F6F0]",
        ghost: 
          "text-[rgba(244,246,240,0.45)] hover:bg-[rgba(200,255,0,0.06)] hover:text-[#F4F6F0]",
        link: 
          "text-[#C8FF00] underline-offset-4 hover:underline",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded px-3 text-xs",
        lg: "h-10 rounded px-8",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

const Button = React.forwardRef(({ className, variant, size, asChild = false, ...props }, ref) => {
  const Comp = asChild ? Slot : "button"
  return (
    <Comp
      className={cn(buttonVariants({ variant, size, className }))}
      ref={ref}
      {...props} />
  );
})
Button.displayName = "Button"

export { Button, buttonVariants }
