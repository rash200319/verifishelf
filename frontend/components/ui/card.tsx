import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export function Card({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-[var(--radius-xl)] border border-[var(--border)] bg-[var(--panel)] p-6 shadow-[var(--shadow-xs)] sm:p-7",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}
