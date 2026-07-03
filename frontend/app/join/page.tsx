"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Users, Mail, ShieldCheck } from "lucide-react";
import { Card } from "@/components/ui/card";
import { DataInput } from "@/components/ui/data-input";
import { TactileButton } from "@/components/ui/tactile-button";
import { apiRequest } from "@/lib/api";

function JoinForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialCode = searchParams.get("code") || "";

  const [inviteCode, setInviteCode] = useState(initialCode);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const submitJoin = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError("");

    try {
      await apiRequest("/auth/join-with-invite", {
        method: "POST",
        body: JSON.stringify({
          full_name: fullName,
          email,
          password,
          invite_code: inviteCode,
        }),
      });

      setSuccess(true);
      setTimeout(() => {
        router.replace("/");
      }, 3000);
    } catch (joinError) {
      setError(joinError instanceof Error ? joinError.message : "Failed to join workspace");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (success) {
    return (
      <Card className="mx-auto w-full max-w-xl text-center p-8 space-y-6">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-[var(--background)] shadow-[var(--shadow-floating)]">
          <ShieldCheck className="h-8 w-8 text-[var(--status-success-text)]" strokeWidth={1.8} />
        </div>
        <div>
          <h2 className="text-2xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">Invite Accepted</h2>
          <p className="mt-2 text-[var(--foreground-muted)]">You have successfully joined the workspace.</p>
        </div>
        <p className="text-sm text-[var(--foreground-muted)]">Redirecting to login...</p>
      </Card>
    );
  }

  return (
    <Card className="mx-auto w-full max-w-xl">
      <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">Join Workspace</p>
      <h2 className="mt-2 text-3xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">Accept your invite.</h2>

      <form className="mt-6 space-y-4" onSubmit={submitJoin}>
        <div className="space-y-1.5 text-left">
          <label className="text-xs font-semibold text-[var(--foreground-muted)] ml-1">Invite Code</label>
          <DataInput value={inviteCode} onChange={(e) => setInviteCode(e.target.value)} placeholder="Enter code" required />
        </div>

        <div className="space-y-1.5 text-left">
          <label className="text-xs font-semibold text-[var(--foreground-muted)] ml-1">Email Address</label>
          <DataInput type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email address (must match invite)" required />
        </div>

        <div className="space-y-1.5 text-left">
          <label className="text-xs font-semibold text-[var(--foreground-muted)] ml-1">Full Name</label>
          <DataInput value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Full name" required />
        </div>

        <div className="space-y-1.5 text-left">
          <label className="text-xs font-semibold text-[var(--foreground-muted)] ml-1">Password</label>
          <DataInput type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Choose a password" required />
        </div>

        <TactileButton type="submit" variant="primary" className="w-full justify-center" disabled={isSubmitting}>
          {isSubmitting ? "Joining..." : "Join Workspace"}
        </TactileButton>
      </form>

      {error ? (
        <div className="mt-4 rounded-[var(--radius-inner)] border border-[rgba(239,68,68,0.2)] bg-[var(--status-error-bg)] px-4 py-3 text-sm text-[var(--status-error-text)]">
          {error}
        </div>
      ) : null}

      <div className="mt-6 text-center space-y-2">
        <p className="text-xs text-[var(--foreground-muted)]">
          Already have an account?{" "}
          <a href="/" onClick={(e) => { e.preventDefault(); router.push("/"); }} className="underline hover:text-[var(--accent)] transition-colors duration-200">
            Sign in here
          </a>
        </p>
      </div>
    </Card>
  );
}

export default function JoinPage() {
  return (
    <div className="relative min-h-screen overflow-hidden px-6 py-10 sm:px-8 lg:px-12 flex items-center justify-center">
      <div className="noise-layer" />
      <div className="grid-overlay" />
      <Suspense fallback={<div className="text-[var(--foreground-muted)]">Loading...</div>}>
        <JoinForm />
      </Suspense>
    </div>
  );
}
