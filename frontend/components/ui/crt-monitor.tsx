import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/utils";

type CrtMonitorProps = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
};

export function CrtMonitor({ className, children, ...props }: CrtMonitorProps) {
  return (
    <div
      className={cn(
        "machine-shell rounded-[28px] border-[4px] border-[rgba(45,52,54,0.92)] bg-[#2a2f36] p-4 shadow-[16px_16px_32px_rgba(0,0,0,0.12),-10px_-10px_24px_rgba(255,255,255,0.4)]",
        className,
      )}
      {...props}
    >
      <div className="mb-3 flex items-center justify-between px-2 text-[0.65rem] font-bold uppercase tracking-[0.22em] text-[var(--foreground-muted)]">
        <span className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-[#22c55e] shadow-[0_0_12px_rgba(34,197,94,0.8)]" />
          System Operational
        </span>
        <span className="monospace text-[var(--foreground-muted)] opacity-75">Torch Proxy Fabric</span>
      </div>
      <div className="machine-screen rounded-[22px] p-4 text-white shadow-[inset_0_0_0_1px_rgba(255,255,255,0.05)]">
        {children}
      </div>
      <div className="mt-3 flex justify-between px-3 text-[0.6rem] font-bold uppercase tracking-[0.25em] text-[var(--foreground-muted)] opacity-60">
        <span>PWR</span>
        <span>MAP / GREY MARKET / COUNTERFEIT</span>
      </div>
    </div>
  );
}
