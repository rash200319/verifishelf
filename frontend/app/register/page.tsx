"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Building2, FileText, Globe, User } from "lucide-react";
import { Card } from "@/components/ui/card";
import { DataInput } from "@/components/ui/data-input";
import { TactileButton } from "@/components/ui/tactile-button";
import { apiRequest } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [brandName, setBrandName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [businessUrl, setBusinessUrl] = useState("");
  const [notes, setNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const submitRegister = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError("");

    try {
      await apiRequest("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          full_name: fullName,
          email,
          password,
          brand_name: brandName,
          company_name: companyName,
          business_url: businessUrl,
          notes,
        }),
      });

      router.replace("/pending");
    } catch (regError) {
      setError(regError instanceof Error ? regError.message : "Registration failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden px-6 py-10 sm:px-8 lg:px-12">
      <div className="noise-layer" />
      <div className="grid-overlay" />

      <div className="relative mx-auto grid min-h-[calc(100vh-5rem)] max-w-7xl gap-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
        <div className="space-y-8">
          <div className="inline-flex items-center gap-3 rounded-full bg-[rgba(255,255,255,0.74)] px-4 py-2 text-[0.7rem] font-bold uppercase tracking-[0.24em] text-[var(--foreground-muted)] shadow-[var(--shadow-card)]">
            <span className="h-2.5 w-2.5 rounded-full bg-[var(--accent)] shadow-[0_0_10px_rgba(255,71,87,0.55)]" />
            VerifyShelf Brand Onboarding
          </div>

          <div className="space-y-5">
            <h1 className="max-w-3xl text-4xl font-extrabold tracking-tight bg-gradient-to-r from-slate-900 via-slate-700 to-indigo-600 bg-clip-text text-transparent dark:from-white dark:to-indigo-400 leading-tight drop-shadow-[0_1px_0_#ffffff] sm:text-5xl">
              Register your brand to start enforcing MAP policies.
            </h1>
            <p className="max-w-2xl text-lg leading-8 text-[var(--foreground-muted)] sm:text-xl">
              Join TorchProxy to protect your margins, monitor unauthorized sellers, and enforce MAP guidelines automatically.
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            {[
              { icon: Building2, title: "Company details", detail: "Tell us about your brand and business." },
              { icon: User, title: "Owner account", detail: "Set up the primary admin for this workspace." },
              { icon: Globe, title: "Review process", detail: "We manually verify brands to ensure security." },
              { icon: FileText, title: "Quick access", detail: "Once approved, you get full dashboard access." },
            ].map((item) => (
              <Card key={item.title} className="p-4">
                <item.icon className="h-6 w-6 text-[var(--accent)]" strokeWidth={1.8} />
                <p className="mt-3 text-sm font-bold text-[var(--foreground)]">{item.title}</p>
                <p className="mt-2 text-sm leading-6 text-[var(--foreground-muted)]">{item.detail}</p>
              </Card>
            ))}
          </div>
        </div>

        <Card className="mx-auto w-full max-w-xl">
          <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">Sign up</p>
          <h2 className="mt-2 text-3xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">Create your workspace.</h2>

          <form className="mt-6 space-y-4" onSubmit={submitRegister}>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5 text-left">
                <label className="text-xs font-semibold text-[var(--foreground-muted)] ml-1">Full Name</label>
                <DataInput value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Full name" required />
              </div>
              <div className="space-y-1.5 text-left">
                <label className="text-xs font-semibold text-[var(--foreground-muted)] ml-1">Email Address</label>
                <DataInput type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email address" required />
              </div>
            </div>

            <div className="space-y-1.5 text-left">
              <label className="text-xs font-semibold text-[var(--foreground-muted)] ml-1">Password</label>
              <DataInput type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" required />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5 text-left">
                <label className="text-xs font-semibold text-[var(--foreground-muted)] ml-1">Brand Name</label>
                <DataInput value={brandName} onChange={(e) => setBrandName(e.target.value)} placeholder="Main brand name" required />
              </div>
              <div className="space-y-1.5 text-left">
                <label className="text-xs font-semibold text-[var(--foreground-muted)] ml-1">Company Name</label>
                <DataInput value={companyName} onChange={(e) => setCompanyName(e.target.value)} placeholder="Legal entity" />
              </div>
            </div>

            <div className="space-y-1.5 text-left">
              <label className="text-xs font-semibold text-[var(--foreground-muted)] ml-1">Business URL</label>
              <DataInput value={businessUrl} onChange={(e) => setBusinessUrl(e.target.value)} placeholder="https://..." />
            </div>

            <div className="space-y-1.5 text-left">
              <label className="text-xs font-semibold text-[var(--foreground-muted)] ml-1">Additional Notes</label>
              <DataInput value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="How did you hear about us? Any specific needs?" />
            </div>

            <TactileButton type="submit" variant="primary" className="w-full justify-center" disabled={isSubmitting}>
              {isSubmitting ? "Submitting..." : "Submit Registration"}
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
      </div>
    </div>
  );
}
