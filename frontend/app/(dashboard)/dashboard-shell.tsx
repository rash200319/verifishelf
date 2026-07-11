"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { FileText, Fingerprint, LayoutDashboard, LogOut, Package, Radar, Settings2, ShieldAlert, ShieldCheck, Sparkles, Menu, X, Users } from "lucide-react";
import { clearSession, loadSession } from "@/lib/session";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/theme-toggle";

const navigationByRole = {
  // A superadmin isn't scoped to any brand -- there's no dashboard,
  // violations, promos, crawl, or reports to show them, just the
  // TorchProxy console where brand registrations get approved.
  superadmin: [{ href: "/admin", label: "TorchProxy", icon: Settings2 }],
  admin: [
    { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
    { href: "/products", label: "Products", icon: Package },
    { href: "/violations", label: "Violations", icon: ShieldAlert },
    { href: "/sellers", label: "Sellers", icon: Fingerprint },
    { href: "/admin", label: "TorchProxy", icon: Settings2 },
    { href: "/settings/invites", label: "Invites", icon: Users },
    { href: "/promos", label: "Promos", icon: Sparkles },
    { href: "/crawl", label: "Crawl Ops", icon: Radar },
    { href: "/reports", label: "Reports", icon: FileText },
  ],
  analyst: [
    { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
    { href: "/violations", label: "Violations", icon: ShieldAlert },
    { href: "/sellers", label: "Sellers", icon: Fingerprint },
    { href: "/promos", label: "Promos", icon: Sparkles },
    { href: "/crawl", label: "Crawl Ops", icon: Radar },
    { href: "/reports", label: "Reports", icon: FileText },
  ],
} as const;

export function DashboardShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [session, setSession] = useState(loadSession());
  const [sidebarOpen, setSidebarOpen] = useState(false);

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
    if (session?.role === "superadmin") {
      return navigationByRole.superadmin;
    }
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
      <div className="flex items-center gap-2.5 px-2 py-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-[var(--accent)] text-[var(--accent-foreground)]">
          <ShieldCheck className="h-4 w-4" strokeWidth={2} />
        </div>
        <div className="flex-1 overflow-hidden">
          <p className="text-[0.65rem] font-medium uppercase tracking-wide text-[var(--foreground-muted)]">
            VerifyShelf
          </p>
          <p className="truncate text-sm font-semibold text-[var(--foreground)]">
            {session?.role === "superadmin" ? "TorchProxy Admin" : session?.brand_name ?? "Workspace"}
          </p>
        </div>
      </div>

      <div className="mt-6 flex-1 space-y-1">
        <p className="px-2 text-xs font-medium uppercase tracking-wide text-[var(--foreground-muted)] mb-2">
          Menu
        </p>
        <nav className="space-y-0.5">
          {navigation.map((item) => {
            const active = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setSidebarOpen(false)}
                className={cn(
                  "flex items-center gap-3 rounded-[var(--radius-md)] px-3 py-2 text-sm font-medium transition-colors",
                  active
                    ? "bg-[var(--accent-soft)] text-[var(--accent)]"
                    : "text-[var(--foreground-muted)] hover:bg-[var(--panel-muted)] hover:text-[var(--foreground)]"
                )}
              >
                <Icon className={cn("h-4 w-4", active ? "text-[var(--accent)]" : "text-[var(--foreground-muted)]")} />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="mt-auto border-t border-[var(--border)] pt-4 space-y-3">
        <div className="flex items-center justify-between px-2">
          <span className="text-xs font-medium text-[var(--foreground-muted)]">Theme</span>
          <ThemeToggle />
        </div>
        <button
          onClick={handleSignOut}
          className="flex w-full items-center gap-3 rounded-[var(--radius-md)] px-3 py-2 text-sm font-medium text-[var(--foreground-muted)] hover:bg-[var(--status-error-bg)] hover:text-[var(--status-error-text)] transition-colors"
        >
          <LogOut className="h-4 w-4" />
          Sign out
        </button>
      </div>
    </>
  );

  return (
    <div className="min-h-screen bg-[var(--background)]">
      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Mobile Header */}
      <div className="sticky top-0 z-30 flex items-center justify-between border-b border-[var(--border)] bg-[var(--panel)] p-4 lg:hidden">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-5 w-5 text-[var(--accent)]" />
          <span className="font-semibold text-[var(--foreground)]">VerifyShelf</span>
        </div>
        <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-1 text-[var(--foreground)]">
          {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      <div className="flex min-h-screen">
        {/* Sidebar */}
        <aside
          className={cn(
            "fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-[var(--border)] bg-[var(--panel)] px-4 py-6 transition-transform duration-200 ease-out lg:static lg:translate-x-0",
            sidebarOpen ? "translate-x-0" : "-translate-x-full"
          )}
        >
          <SidebarContent />
        </aside>

        {/* Main Content */}
        <main className="flex-1 lg:pl-8 lg:pr-8 xl:pr-12 lg:pt-8 overflow-y-auto">
          <div className="mx-auto max-w-6xl p-4 sm:p-6 lg:p-0">
            {!session ? (
              <div className="mb-8 rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--panel)] px-5 py-4 text-sm text-[var(--foreground-muted)]">
                No saved session found. Sign in from the home page before using the protected screens.
              </div>
            ) : null}

            <div className="min-h-[calc(100vh-8rem)]">
              {children}
            </div>

            <footer className="mt-12 flex items-center justify-between border-t border-[var(--border)] py-6 text-xs text-[var(--foreground-muted)]">
              <p className="font-semibold">VerifyShelf</p>
              <p>© {new Date().getFullYear()} VerifyShelf Inc.</p>
            </footer>
          </div>
        </main>
      </div>
    </div>
  );
}
