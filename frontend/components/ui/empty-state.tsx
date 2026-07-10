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
    <div className={cn("flex flex-col items-center justify-center rounded-[var(--radius-lg)] border border-dashed border-[var(--border)] p-8 text-center", className)}>
      <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-[var(--panel-muted)]">
        <Icon className="h-5 w-5 text-[var(--foreground-muted)]" strokeWidth={1.5} />
      </div>
      <p className="text-sm font-medium text-[var(--foreground)]">{title}</p>
      <p className="mt-1 max-w-sm text-sm leading-6 text-[var(--foreground-muted)]">{description}</p>
    </div>
  );
}
