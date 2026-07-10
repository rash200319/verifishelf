import type { SelectHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export function Select({ className, children, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(
        "h-10 w-full rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--panel)] px-3 text-sm text-[var(--foreground)] transition-colors focus:outline-none focus:border-[var(--accent)] focus:shadow-[var(--shadow-focus)]",
        className,
      )}
      {...props}
    >
      {children}
    </select>
  );
}
