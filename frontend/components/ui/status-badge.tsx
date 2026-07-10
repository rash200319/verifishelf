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
    success: "bg-[var(--status-success-bg)] text-[var(--status-success-text)]",
    error: "bg-[var(--status-error-bg)] text-[var(--status-error-text)]",
    warning: "bg-[var(--status-warning-bg)] text-[var(--status-warning-text)]",
    neutral: "bg-[var(--status-neutral-bg)] text-[var(--status-neutral-text)]",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        typeStyles[resolvedType],
        className
      )}
    >
      {status}
    </span>
  );
}
