import { FileWarning, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  className?: string;
}

export function EmptyState({ icon: Icon = FileWarning, title, description, className }: EmptyStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center rounded-[var(--radius-inner)] bg-[var(--bg-inner)] p-8 text-center shadow-[inset_0_0_0_1px_rgba(255,255,255,0.1)]", className)}>
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-[var(--background)] shadow-[var(--shadow-recessed)]">
        <Icon className="h-6 w-6 text-[var(--foreground-muted)]" strokeWidth={1.5} />
      </div>
      <p className="text-sm font-bold text-[var(--foreground)]">{title}</p>
      <p className="mt-1 max-w-sm text-sm leading-6 text-[var(--foreground-muted)]">{description}</p>
    </div>
  );
}
