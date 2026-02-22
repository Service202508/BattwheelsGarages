import * as React from "react"

import { cn } from "@/lib/utils"

const Input = React.forwardRef(({ className, type, ...props }, ref) => {
  return (
    <input
      type={type}
      className={cn(
        "flex h-9 w-full rounded border border-[rgba(255,255,255,0.07)] bg-[#111820] px-3 py-1 text-base text-[#F4F6F0] transition-all file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-[#F4F6F0] placeholder:text-[rgba(244,246,240,0.25)] focus-visible:outline-none focus-visible:border-[#C8FF00] focus-visible:ring-[3px] focus-visible:ring-[rgba(200,255,0,0.08)] disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
        className
      )}
      ref={ref}
      {...props} />
  );
})
Input.displayName = "Input"

export { Input }
