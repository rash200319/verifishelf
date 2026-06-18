"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { usePathname } from "next/navigation";
import { useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { Building2, FileText, LayoutDashboard, LogOut, Radar, Settings2, ShieldCheck, Sparkles } from "lucide-react";
import { clearSession, loadSession } from "@/lib/session";
import { cn } from "@/lib/utils";

const navigationByRole = {
  admin: [
    { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
    { href: "/admin", label: "TorchProxy", icon: Settings2 },
    { href: "/promos", label: "Promos", icon: Sparkles },
    { href: "/crawl", label: "Crawl Ops", icon: Radar },
    { href: "/reports", label: "Reports", icon: FileText },
  ],
  analyst: [
    { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
    { href: "/promos", label: "Promos", icon: Sparkles },
    { href: "/crawl", label: "Crawl Ops", icon: Radar },
    { href: "/reports", label: "Reports", icon: FileText },
  ],
} as const;

export function DashboardShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [session, setSession] = useState(loadSession());

  useEffect(() => {
    const syncSession = () => setSession(loadSession());
    window.addEventListener("storage", syncSession);
    window.addEventListener("verifishelf-session", syncSession as EventListener);
    return () => {
      window.removeEventListener("storage", syncSession);
      window.removeEventListener("verifishelf-session", syncSession as EventListener);
    };
  }, []);

  const navigation = useMemo(() => {
    if (session?.role === "admin") {
      return navigationByRole.admin;
    }

    return navigationByRole.analyst;
  }, [session?.role]);

  if (pathname === "/") {
    return <>{children}</>;
  }

  const handleSignOut = () => {
    clearSession();
    setSession(null);
    window.dispatchEvent(new Event("verifishelf-session"));
    router.replace("/");
  };

  return (
    <div className="relative min-h-screen">
      <div className="noise-layer" />
      <div className="grid-overlay" />

      <div className="relative mx-auto flex min-h-screen max-w-7xl flex-col px-6 pb-10 pt-6 sm:px-8 lg:px-12">
        <header className="machine-shell sticky top-4 z-30 mb-8 rounded-[var(--radius-2xl)] px-5 py-4 backdrop-blur-sm sm:px-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-[18px] bg-[var(--foreground)] text-[var(--accent-foreground)] shadow-[var(--shadow-sharp)]">
                <ShieldCheck className="h-7 w-7" strokeWidth={1.9} />
              </div>
              <div>
                <p className="monospace text-[0.68rem] font-bold uppercase tracking-[0.3em] text-[var(--foreground-muted)]">
                  VerifyShelf
                </p>
                <h1 className="text-lg font-extrabold tracking-[-0.03em] text-[var(--foreground)] sm:text-xl">
                  {session?.brandName ?? session?.brand_name ?? "Role-based operations console"}
                </h1>
                <p className="text-sm text-[var(--foreground-muted)]">
                  {session?.role === "admin"
                    ? "TorchProxy onboarding and user provisioning"
                    : "Brand workspace for promos, crawl tracking, and reports"}
                </p>
              </div>
            </div>

            <nav className="flex flex-wrap gap-2">
              {navigation.map((item) => {
                const active = pathname === item.href;
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "machine-floating inline-flex items-center gap-2 rounded-full px-4 py-2 text-[0.68rem] font-bold uppercase tracking-[0.2em] transition hover:text-[var(--foreground)]",
                      active ? "bg-[var(--foreground)] text-[var(--accent-foreground)]" : "text-[var(--foreground-muted)]",
                    )}
                  >
                    <Icon className="h-3.5 w-3.5" strokeWidth={2} />
                    {item.label}
                  </Link>
                );
              })}
              <button
                type="button"
                onClick={handleSignOut}
                className="machine-floating inline-flex items-center gap-2 rounded-full px-4 py-2 text-[0.68rem] font-bold uppercase tracking-[0.2em] text-[var(--foreground-muted)] transition hover:text-[var(--foreground)]"
              >
                <LogOut className="h-3.5 w-3.5" strokeWidth={2} />
                Sign out
              </button>
            </nav>
          </div>
        </header>

        {!session ? (
          <div className="mb-8 rounded-[var(--radius-lg)] border border-[rgba(255,71,87,0.18)] bg-[rgba(255,255,255,0.56)] px-5 py-4 text-sm text-[var(--foreground-muted)] shadow-[var(--shadow-card)]">
            No saved session found. Sign in from the home page before using the protected screens.
          </div>
        ) : null}

        <div className="flex-1">{children}</div>

        <footer className="mt-10 flex flex-col gap-3 border-t border-[rgba(74,85,104,0.12)] pt-6 text-sm text-[var(--foreground-muted)] sm:flex-row sm:items-center sm:justify-between">
          <p className="monospace text-[0.7rem] font-bold uppercase tracking-[0.28em]">VerifyShelf</p>
          <p>One role gets provisioning. Every brand gets live promos, crawl status, and weekly reporting.</p>
        </footer>
      </div>
    </div>
  );
}
