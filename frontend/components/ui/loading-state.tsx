import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface LoadingStateProps {
  text?: string;
  className?: string;
}

export function LoadingState({ text = "Loading data...", className }: LoadingStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center p-8 text-center", className)}>
      <Loader2 className="mb-3 h-5 w-5 animate-spin text-[var(--accent)]" />
      <p className="text-sm text-[var(--foreground-muted)]">{text}</p>
    </div>
  );
}
