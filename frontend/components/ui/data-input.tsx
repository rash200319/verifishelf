import type { InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export function DataInput({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-10 w-full rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--panel)] px-3 text-sm text-[var(--foreground)] placeholder:text-[var(--foreground-muted)] transition-colors focus:outline-none focus:border-[var(--accent)] focus:shadow-[var(--shadow-focus)]",
        className,
      )}
      {...props}
    />
  );
}
