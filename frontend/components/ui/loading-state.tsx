import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface LoadingStateProps {
  text?: string;
  className?: string;
}

export function LoadingState({ text = "Loading data...", className }: LoadingStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center p-8 text-center", className)}>
      <div className="relative mb-4 flex h-12 w-12 items-center justify-center">
        <div className="absolute inset-0 rounded-full border-2 border-[var(--muted)] opacity-20" />
        <Loader2 className="h-6 w-6 animate-spin text-[var(--accent)]" />
      </div>
      <p className="text-sm font-semibold text-[var(--foreground-muted)]">{text}</p>
    </div>
  );
}
