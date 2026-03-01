import * as React from "react"

import { cn } from "@/lib/utils"

const Input = React.forwardRef(({ className, type, ...props }, ref) => {
  return (
    <input
      type={type}
      className={cn(
        "flex h-9 w-full rounded border border-white/[0.07] bg-bw-panel px-3 py-1 text-base text-bw-white transition-all file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-bw-white placeholder:text-bw-white/25 focus-visible:outline-none focus-visible:border-bw-volt focus-visible:ring-[3px] focus-visible:ring-bw-volt/[0.08] disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
        className
      )}
      ref={ref}
      {...props} />
  );
})
Input.displayName = "Input"

export { Input }
