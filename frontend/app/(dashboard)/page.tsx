"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Building2, KeyRound, ShieldCheck } from "lucide-react";
import { Card } from "@/components/ui/card";
import { DataInput } from "@/components/ui/data-input";
import { TactileButton } from "@/components/ui/tactile-button";
import { apiRequest } from "@/lib/api";
import type { LoginResponse, SessionData } from "@/lib/backend-types";
import { loadSession, saveSession } from "@/lib/session";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@verifishelf.local");
  const [password, setPassword] = useState("admin123");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const existingSession = loadSession();
    if (existingSession?.role === "analyst") {
      router.replace("/dashboard");
    }
  }, [router]);

  const submitLogin = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError("");

    try {
      const response = await apiRequest<LoginResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email,
          password,
        }),
      });

      const session: SessionData = {
        ...response,
        email,
      };

      saveSession(session);
      window.dispatchEvent(new Event("verifishelf-session"));
      // A superadmin has no brand, so /dashboard (which assumes one) makes
      // no sense for them -- send them straight to the TorchProxy console.
      router.replace(session.role === "superadmin" ? "/admin" : "/dashboard");
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : "Login failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen px-6 py-10 sm:px-8 lg:px-12">
      <div className="mx-auto grid min-h-[calc(100vh-5rem)] max-w-6xl gap-10 lg:grid-cols-[1fr_0.9fr] lg:items-center">
        <div className="space-y-8">
          <div className="inline-flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--panel)] px-3 py-1.5 text-xs font-medium text-[var(--foreground-muted)]">
            <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent)]" />
            VerifyShelf brand login
          </div>

          <div className="space-y-4">
            <h1 className="max-w-xl text-4xl font-semibold tracking-tight text-[var(--foreground)] sm:text-5xl">
              Access your MAP enforcement workspace.
            </h1>
            <p className="max-w-lg text-lg leading-7 text-[var(--foreground-muted)]">
              Monitor your product catalog, manage approved promos, and review weekly violation reports.
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            {[
              { icon: ShieldCheck, title: "Secure access", detail: "Backend token-based login for secure authorization." },
              { icon: Building2, title: "Brand scoped", detail: "Every session is tied to one brand tenant." },
              { icon: KeyRound, title: "Direct login", detail: "No extra onboarding flow on this public portal." },
            ].map((item) => (
              <Card key={item.title} className="p-4">
                <item.icon className="h-5 w-5 text-[var(--accent)]" strokeWidth={1.8} />
                <p className="mt-3 text-sm font-semibold text-[var(--foreground)]">{item.title}</p>
                <p className="mt-1.5 text-sm leading-5 text-[var(--foreground-muted)]">{item.detail}</p>
              </Card>
            ))}
          </div>
        </div>

        <Card className="mx-auto w-full max-w-md">
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--foreground-muted)]">Sign in</p>
          <h2 className="mt-1.5 text-2xl font-semibold tracking-tight text-[var(--foreground)]">Enter your workspace details.</h2>

          <form className="mt-6 space-y-4" onSubmit={submitLogin}>
            <div className="space-y-1.5 text-left">
              <label htmlFor="email-input" className="text-xs font-medium text-[var(--foreground-muted)]">
                Email Address
              </label>
              <DataInput
                id="email-input"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="Email address"
                aria-label="Email address"
                required
              />
            </div>

            <div className="space-y-1.5 text-left">
              <label htmlFor="password-input" className="text-xs font-medium text-[var(--foreground-muted)]">
                Password
              </label>
              <DataInput
                id="password-input"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Password"
                aria-label="Password"
                required
              />
            </div>

            <TactileButton type="submit" variant="primary" className="w-full justify-center" disabled={isSubmitting}>
              {isSubmitting ? "Signing In..." : "Open Workspace"}
            </TactileButton>
          </form>

          {error ? (
            <div className="mt-4 rounded-[var(--radius-md)] bg-[var(--status-error-bg)] px-4 py-3 text-sm text-[var(--status-error-text)]">
              {error}
            </div>
          ) : null}

          <div className="mt-6 text-center space-y-2">
            <a
              href="#"
              onClick={(e) => e.preventDefault()}
              className="text-xs font-medium text-[var(--foreground-muted)] hover:text-[var(--accent)] transition-colors"
            >
              Forgot Password?
            </a>
            <p className="text-xs text-[var(--foreground-muted)]">
              Need help accessing your workspace?{" "}
              <a
                href="#"
                onClick={(e) => e.preventDefault()}
                className="underline hover:text-[var(--accent)] transition-colors"
              >
                Contact support
              </a>
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
}
