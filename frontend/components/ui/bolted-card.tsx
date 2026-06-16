import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

function Bolt() {
  return (
    <span className="absolute h-3 w-3 rounded-full bg-[var(--muted)] shadow-[inset_1px_1px_2px_rgba(0,0,0,0.25),inset_-1px_-1px_1px_rgba(255,255,255,0.85)]" />
  );
}

export function BoltedCard({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "machine-shell relative overflow-hidden rounded-[var(--radius-lg)] p-6 transition-transform duration-300 ease-out hover:-translate-y-1 hover:shadow-[var(--shadow-floating)] sm:p-8",
        className,
      )}
      {...props}
    >
      <span className="pointer-events-none absolute left-4 top-4"><Bolt /></span>
      <span className="pointer-events-none absolute right-4 top-4"><Bolt /></span>
      <span className="pointer-events-none absolute left-4 bottom-4"><Bolt /></span>
      <span className="pointer-events-none absolute right-4 bottom-4"><Bolt /></span>
      <div className="pointer-events-none absolute right-5 top-5 flex gap-1 opacity-70">
        <span className="h-6 w-1 rounded-full bg-[var(--muted)] shadow-[inset_1px_1px_2px_rgba(0,0,0,0.14)]" />
        <span className="h-6 w-1 rounded-full bg-[var(--muted)] shadow-[inset_1px_1px_2px_rgba(0,0,0,0.14)]" />
        <span className="h-6 w-1 rounded-full bg-[var(--muted)] shadow-[inset_1px_1px_2px_rgba(0,0,0,0.14)]" />
      </div>
      {children}
    </div>
  );
}
