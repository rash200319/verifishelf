"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { Building2, FileText, LayoutDashboard, LogOut, Radar, Settings2, ShieldCheck, Sparkles, Menu, X, Users } from "lucide-react";
import { clearSession, loadSession } from "@/lib/session";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/theme-toggle";

const navigationByRole = {
  admin: [
    { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
    { href: "/admin", label: "TorchProxy", icon: Settings2 },
    { href: "/settings/invites", label: "Invites", icon: Users },
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
  const [session, setSession] = useState<ReturnType<typeof loadSession>>(null);
  const [mounted, setMounted] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    setMounted(true);
    setSession(loadSession());
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

  const SidebarContent = () => (
    <>
      <div className="flex items-center gap-3 px-2 py-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[12px] bg-[var(--foreground)] text-[var(--accent-foreground)] shadow-[var(--shadow-sharp)]">
          <ShieldCheck className="h-5 w-5" strokeWidth={2} />
        </div>
        <div className="flex-1 overflow-hidden">
          <p className="monospace text-[0.6rem] font-bold uppercase tracking-[0.2em] text-[var(--foreground-muted)]">
            VerifyShelf
          </p>
          <p className="truncate text-sm font-bold text-[var(--foreground)]">
            {mounted && session?.brand_name ? session.brand_name : "Workspace"}
          </p>
        </div>
      </div>

      <div className="mt-8 flex-1 space-y-2">
        <p className="px-2 text-xs font-semibold text-[var(--foreground-muted)] uppercase tracking-wider mb-2">
          Menu
        </p>
        <nav className="space-y-1.5">
          {navigation.map((item) => {
            const active = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setSidebarOpen(false)}
                className={cn(
                  "flex items-center gap-3 rounded-[var(--radius-md)] px-3 py-2.5 text-sm font-medium transition-colors",
                  active
                    ? "bg-[rgba(79,70,229,0.1)] text-[var(--accent)]"
                    : "text-[var(--foreground-muted)] hover:bg-[rgba(0,0,0,0.05)] dark:hover:bg-[rgba(255,255,255,0.05)] hover:text-[var(--foreground)]"
                )}
              >
                <Icon className={cn("h-4 w-4", active ? "text-[var(--accent)]" : "text-[var(--foreground-muted)]")} />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="mt-auto border-t border-[rgba(148,163,184,0.2)] pt-4 space-y-4">
        <div className="flex items-center justify-between px-2">
          <span className="text-xs font-medium text-[var(--foreground-muted)]">Theme</span>
          <ThemeToggle />
        </div>
        <button
          onClick={handleSignOut}
          className="flex w-full items-center gap-3 rounded-[var(--radius-md)] px-3 py-2.5 text-sm font-medium text-[var(--foreground-muted)] hover:bg-[rgba(239,68,68,0.1)] hover:text-red-500 transition-colors"
        >
          <LogOut className="h-4 w-4" />
          Sign out
        </button>
      </div>
    </>
  );

  return (
    <div className="relative min-h-screen bg-[var(--background)]">
      <div className="noise-layer" />
      <div className="grid-overlay" />

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Mobile Header */}
      <div className="sticky top-0 z-30 flex items-center justify-between border-b border-[rgba(148,163,184,0.2)] bg-[var(--background)]/80 p-4 backdrop-blur-md lg:hidden">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-6 w-6 text-[var(--foreground)]" />
          <span className="font-bold text-[var(--foreground)]">VerifyShelf</span>
        </div>
        <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-1 text-[var(--foreground)]">
          {sidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      <div className="flex min-h-screen">
        {/* Sidebar */}
        <aside
          className={cn(
            "fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-[rgba(148,163,184,0.2)] bg-[var(--panel)] px-4 py-6 transition-transform duration-300 ease-in-out lg:static lg:translate-x-0 shadow-[var(--shadow-sharp)] lg:shadow-none",
            sidebarOpen ? "translate-x-0" : "-translate-x-full"
          )}
        >
          <SidebarContent />
        </aside>

        {/* Main Content */}
        <main className="flex-1 lg:pl-8 lg:pr-8 xl:pr-12 lg:pt-8 relative overflow-y-auto">
          <div className="mx-auto max-w-6xl p-4 sm:p-6 lg:p-0">
            {mounted && !session ? (
              <div className="mb-8 rounded-[var(--radius-lg)] border border-[rgba(255,71,87,0.18)] bg-[rgba(255,255,255,0.56)] px-5 py-4 text-sm text-[var(--foreground-muted)] shadow-[var(--shadow-card)]">
                No saved session found. Sign in from the home page before using the protected screens.
              </div>
            ) : null}

            <div className="min-h-[calc(100vh-8rem)]">
              {children}
            </div>

            <footer className="mt-12 flex items-center justify-between border-t border-[rgba(148,163,184,0.2)] py-6 text-xs text-[var(--foreground-muted)]">
              <p className="monospace font-bold uppercase tracking-[0.15em]">VerifyShelf</p>
              <p>© {new Date().getFullYear()} VerifyShelf Inc.</p>
            </footer>
          </div>
        </main>
      </div>
    </div>
  );
}
