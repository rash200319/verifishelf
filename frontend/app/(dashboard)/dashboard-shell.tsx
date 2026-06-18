"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { ShieldCheck } from "lucide-react";

const navigation = [
  { href: "/", label: "Overview" },
  { href: "/onboarding", label: "Onboarding" },
  { href: "/violations", label: "Violations" },
  { href: "/reports", label: "Reports" },
  { href: "/pricing", label: "Pricing" },
];

export function DashboardShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="relative min-h-screen">
      <div className="noise-layer" />
      <div className="grid-overlay" />

      <div className="relative mx-auto flex min-h-screen max-w-7xl flex-col px-6 pb-10 pt-6 sm:px-8 lg:px-12">
        <header className="machine-shell sticky top-4 z-30 mb-8 rounded-[var(--radius-2xl)] px-5 py-4 backdrop-blur-sm sm:px-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center gap-5">
              <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-[18px] bg-[var(--foreground)] text-[var(--accent-foreground)] shadow-[var(--shadow-sharp)]">
                <ShieldCheck className="h-7 w-7" strokeWidth={1.9} />
              </div>
              <div className="pl-1.5">
                <p className="monospace text-[0.68rem] font-bold uppercase tracking-[0.3em] text-[var(--foreground-muted)]">
                  VerifyShelf
                </p>
                <h1 className="text-lg font-extrabold tracking-[-0.03em] text-[var(--foreground)] sm:text-xl">
                  Real-Time Brand Protection <span className="hidden xl:inline">& MAP Violation Detection</span>
                </h1>
              </div>
            </div>

            <nav className="flex flex-wrap items-center gap-2">
              {navigation.map((item) => {
                const active = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "machine-floating rounded-full px-4 py-2 text-[0.68rem] font-bold uppercase tracking-[0.2em] transition hover:text-[var(--foreground)]",
                      active ? "bg-[var(--foreground)] text-[var(--accent-foreground)]" : "text-[var(--foreground-muted)]",
                    )}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </div>
        </header>

        <div className="flex-1">{children}</div>

        <footer className="mt-10 flex flex-col gap-3 border-t border-[rgba(74,85,104,0.12)] pt-6 text-sm text-[var(--foreground-muted)] sm:flex-row sm:items-center sm:justify-between">
          <p className="monospace text-[0.7rem] font-bold uppercase tracking-[0.28em]">VerifyShelf</p>
          <p>Real-time brand protection, MAP monitoring, and automated seller tracking.</p>
        </footer>
      </div>
    </div>
  );
}
