import { cn } from "@/lib/utils";

type Status = "success" | "error" | "warning" | "neutral";

export function getStatusType(statusText: string): Status {
  const s = statusText.toLowerCase();
  if (s.includes("completed") || s.includes("active") || s.includes("success")) return "success";
  if (s.includes("failed") || s.includes("error") || s.includes("rejected")) return "error";
  if (s.includes("running") || s.includes("pending") || s.includes("processing")) return "warning";
  return "neutral";
}

interface StatusBadgeProps {
  status: string;
  type?: Status;
  className?: string;
}

export function StatusBadge({ status, type, className }: StatusBadgeProps) {
  const resolvedType = type || getStatusType(status);

  const typeStyles = {
    success: "bg-[var(--status-success-bg)] text-[var(--status-success-text)] border-[rgba(34,197,94,0.2)]",
    error: "bg-[var(--status-error-bg)] text-[var(--status-error-text)] border-[rgba(239,68,68,0.2)]",
    warning: "bg-[var(--status-warning-bg)] text-[var(--status-warning-text)] border-[rgba(245,158,11,0.2)]",
    neutral: "bg-[var(--status-neutral-bg)] text-[var(--status-neutral-text)] border-[rgba(148,163,184,0.2)]",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-3 py-1 text-[0.65rem] font-bold uppercase tracking-[0.22em]",
        typeStyles[resolvedType],
        className
      )}
    >
      {status}
    </span>
  );
}
