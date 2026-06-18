import type { InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export function DataInput({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "machine-recessed h-14 w-full rounded-[var(--radius-md)] border-0 px-4 font-mono text-sm text-[var(--foreground)] placeholder:text-[rgba(74,85,104,0.55)] focus:outline-none focus:shadow-[var(--shadow-recessed),0_0_0_2px_var(--accent)]",
        className,
      )}
      {...props}
    />
  );
}
