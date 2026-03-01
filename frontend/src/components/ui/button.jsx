import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva } from "class-variance-authority";

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-bw-volt/30 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "bg-bw-volt text-bw-black font-bold hover:bg-bw-volt-hover hover:shadow-[0_0_20px_rgba(200,255,0,0.3)]",
        destructive:
          "bg-bw-red/10 text-bw-red border border-bw-red/20 hover:bg-bw-red/15",
        outline:
          "border border-white/[0.13] text-bw-white/70 hover:border-bw-volt/30 hover:text-bw-white",
        secondary:
          "bg-bw-panel text-bw-white/70 border border-white/[0.07] hover:bg-bw-volt/[0.06] hover:text-bw-white",
        ghost: 
          "text-bw-white/[0.45] hover:bg-bw-volt/[0.06] hover:text-bw-white",
        link: 
          "text-bw-volt underline-offset-4 hover:underline",
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
