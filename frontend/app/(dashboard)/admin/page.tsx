"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Building2, CheckCircle2, KeyRound, PlusCircle, ShieldCheck, UserPlus, Check, X } from "lucide-react";
import { Card } from "@/components/ui/card";
import { DataInput } from "@/components/ui/data-input";
import { TactileButton } from "@/components/ui/tactile-button";
import { apiRequest } from "@/lib/api";
import type { BrandOnboardResponse, CreateUserResponse, SessionData, PendingBrand, PendingBrandsResponse } from "@/lib/backend-types";
import { clearSession, loadSession } from "@/lib/session";
import { formatDateTime } from "@/lib/format";

const planOptions = [
  { value: "starter", label: "Starter" },
  { value: "growth", label: "Growth" },
  { value: "enterprise", label: "Enterprise" },
] as const;

export default function AdminPage() {
  const router = useRouter();
  const [session, setSession] = useState<SessionData | null>(null);
  const [mounted, setMounted] = useState(false);
  const [brandName, setBrandName] = useState("");
  const [plan, setPlan] = useState<(typeof planOptions)[number]["value"]>("starter");
  const [brandResult, setBrandResult] = useState<BrandOnboardResponse["brand"] | null>(null);
  const [brandMessage, setBrandMessage] = useState("");
  const [brandSubmitting, setBrandSubmitting] = useState(false);

  const [brandId, setBrandId] = useState("");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("analyst");
  const [userResult, setUserResult] = useState<CreateUserResponse["user"] | null>(null);
  const [userMessage, setUserMessage] = useState("");
  const [userSubmitting, setUserSubmitting] = useState(false);

  const [pendingBrands, setPendingBrands] = useState<PendingBrand[]>([]);
  const [pendingLoading, setPendingLoading] = useState(false);
  const [isTorchproxyAdmin, setIsTorchproxyAdmin] = useState(false);

  const fetchPendingBrands = useCallback(async () => {
    if (!session) return;
    setPendingLoading(true);
    try {
      const response = await apiRequest<PendingBrandsResponse>("/admin/torchproxy/brands/pending", { session });
      setPendingBrands(response.brands || []);
    } catch (error) {
      console.error("Failed to fetch pending brands", error);
    } finally {
      setPendingLoading(false);
    }
  }, [session]);

  const checkTorchproxyAdminAccess = useCallback(async () => {
    if (!session) return;
    try {
      await apiRequest<PendingBrandsResponse>("/admin/torchproxy/brands/pending", { session });
      setIsTorchproxyAdmin(true);
      await fetchPendingBrands();
    } catch (error) {
      // If this fails, they're a brand admin, not a TorchProxy admin
      setIsTorchproxyAdmin(false);
      // Pre-fill brand ID and name for brand admins
      setBrandId(String(session.brand_id));
      setBrandName(session.brand_name || "");
    }
  }, [session, fetchPendingBrands]);

  useEffect(() => {
    if (session?.role === "admin") {
      // Check if this is a TorchProxy admin by trying to fetch pending brands
      // If it fails with 403, they're a brand admin, not a TorchProxy admin
      checkTorchproxyAdminAccess();
    }
  }, [session, checkTorchproxyAdminAccess]);

  const handleBrandAction = async (brandId: number, action: 'approve' | 'reject') => {
    if (!session) return;
    try {
      await apiRequest(`/admin/torchproxy/brands/${brandId}/${action}`, {
        method: "POST",
        session,
        body: JSON.stringify({
          reviewed_by: session.email || "admin",
          review_notes: "Processed via dashboard"
        })
      });
      fetchPendingBrands();
    } catch (error) {
      console.error(`Failed to ${action} brand`, error);
    }
  };

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

  useEffect(() => {
    if (!mounted) return;
    if (!session) {
      router.replace("/");
      return;
    }

    // Allow both brand admins and TorchProxy admins to access this page
    // The UI will show different sections based on access level
    if (session.role !== "admin") {
      router.replace("/dashboard");
    }
  }, [router, session, mounted]);

  const signOut = () => {
    clearSession();
    setSession(null);
    window.dispatchEvent(new Event("verifishelf-session"));
    router.replace("/");
  };

  const onboardBrand = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!session) return;

    setBrandSubmitting(true);
    setBrandMessage("");

    try {
      const endpoint = isTorchproxyAdmin ? "/admin/torchproxy/onboard" : "/admin/onboard-my-brand";
      const response = await apiRequest<BrandOnboardResponse>(endpoint, {
        method: "POST",
        session,
        body: JSON.stringify({ name: brandName, plan }),
      });

      setBrandResult(response.brand);
      setBrandId(String(response.brand.id));
      setBrandMessage(`Brand ${response.brand.name} onboarded successfully with Torch sub-account ${response.brand.torch_sub_id}.`);
      if (!isTorchproxyAdmin) {
        // Brand admins don't clear the brand name since it's their brand
        setBrandName(session.brand_name || "");
      } else {
        setBrandName("");
      }
    } catch (error) {
      setBrandMessage(error instanceof Error ? error.message : "Brand onboarding failed");
    } finally {
      setBrandSubmitting(false);
    }
  };

  const createUser = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!session) return;

    setUserSubmitting(true);
    setUserMessage("");

    try {
      const response = await apiRequest<CreateUserResponse>("/admin/users/create", {
        method: "POST",
        session,
        body: JSON.stringify({
          brand_id: Number(brandId),
          full_name: fullName,
          email,
          password,
          role,
        }),
      });

      setUserResult(response.user);
      setUserMessage(`Created ${response.user.full_name} for brand ${response.user.brand_id}.`);
      setFullName("");
      setEmail("");
      setPassword("");
      setRole("analyst");
    } catch (error) {
      setUserMessage(error instanceof Error ? error.message : "User creation failed");
    } finally {
      setUserSubmitting(false);
    }
  };

  if (!session || session.role !== "admin") {
    return (
      <section className="space-y-6 pb-10">
        <Card>
          <p className="monospace text-[0.7rem] font-bold uppercase tracking-[0.28em] text-[var(--foreground-muted)]">Access restricted</p>
          <h2 className="mt-2 text-3xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">Admin access required.</h2>
          <p className="mt-3 max-w-2xl text-lg leading-8 text-[var(--foreground-muted)]">
            Sign in with an admin account to access this page.
          </p>
          <div className="mt-6">
            <TactileButton variant="primary" onClick={signOut}>
              Back to login
            </TactileButton>
          </div>
        </Card>
      </section>
    );
  }

  const currentSession = session;

  return (
    <section className="space-y-8 pb-10">
      <div className="max-w-4xl space-y-3">
        <p className="monospace text-[0.7rem] font-bold uppercase tracking-[0.28em] text-[var(--foreground-muted)]">
          {isTorchproxyAdmin ? "TorchProxy console" : "Brand admin console"}
        </p>
        <h2 className="text-4xl font-extrabold tracking-[-0.04em] text-[var(--foreground)] sm:text-5xl">
          {isTorchproxyAdmin ? "Review and approve brand registrations." : "Onboard your brand to VerifyShelf."}
        </h2>
        <p className="max-w-3xl text-lg leading-8 text-[var(--foreground-muted)]">
          {isTorchproxyAdmin 
            ? "Review pending brand applications and approve them for platform access."
            : "Complete your brand onboarding to start monitoring MAP compliance across marketplaces."
          }
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {[
          { icon: ShieldCheck, title: "Admin token", detail: `Signed in as ${currentSession.email ?? currentSession.brand_name}` },
          ...(isTorchproxyAdmin ? [{ icon: Building2, title: "Brand approvals", detail: "Review and approve pending brand registrations." }] : [{ icon: Building2, title: "Brand onboarding", detail: "Configure your brand and select your plan." }]),
          ...(isTorchproxyAdmin ? [] : [{ icon: UserPlus, title: "Team management", detail: "Add team members to your brand workspace." }]),
        ].map((item) => (
          <Card key={item.title}>
            <item.icon className="h-6 w-6 text-[var(--accent)]" strokeWidth={1.8} />
            <p className="mt-3 text-sm font-bold text-[var(--foreground)]">{item.title}</p>
            <p className="mt-2 text-sm leading-6 text-[var(--foreground-muted)]">{item.detail}</p>
          </Card>
        ))}
      </div>

      {isTorchproxyAdmin && (
        <div className="mb-8">
          <div className="flex items-start gap-4 mb-6">
            <div>
              <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">Pending Registrations</p>
              <h3 className="mt-1 text-2xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">Review brand applications.</h3>
            </div>
          </div>

          {pendingLoading ? (
            <p className="text-sm text-[var(--foreground-muted)]">Loading pending brands...</p>
          ) : pendingBrands.length === 0 ? (
            <Card className="p-6 text-center text-sm text-[var(--foreground-muted)]">No pending brand registrations.</Card>
          ) : (
            <div className="grid gap-4">
              {pendingBrands.map((b) => (
                <Card key={b.id} className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <p className="font-bold text-[var(--foreground)]">{b.name}</p>
                    <p className="text-sm text-[var(--foreground-muted)]">{b.company_name} - {b.business_url}</p>
                    <p className="text-xs text-[var(--foreground-muted)] mt-1">Notes: {b.onboarding_notes}</p>
                  </div>
                  <div className="flex gap-2">
                    <TactileButton variant="primary" onClick={() => handleBrandAction(b.id, 'approve')} className="flex items-center gap-2">
                      <Check className="h-4 w-4" /> Approve
                    </TactileButton>
                    <TactileButton variant="secondary" onClick={() => handleBrandAction(b.id, 'reject')} className="flex items-center gap-2 text-[var(--status-error-text)] hover:text-[var(--status-error-text)] border border-[rgba(239,68,68,0.2)]">
                      <X className="h-4 w-4" /> Reject
                    </TactileButton>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      <div className={`grid gap-6 ${isTorchproxyAdmin ? 'hidden' : 'max-w-2xl'}`}>
        <Card>
          <div className="flex items-start gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--background)] shadow-[var(--shadow-floating)]">
              <PlusCircle className="h-7 w-7 text-[var(--accent)]" strokeWidth={1.8} />
            </div>
            <div>
              <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">Brand onboarding</p>
              <h3 className="mt-1 text-2xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">Complete your brand setup.</h3>
            </div>
          </div>

          <form className="mt-6 space-y-3" onSubmit={onboardBrand}>
            <div className="space-y-1.5 text-left">
              <label className="text-xs font-semibold text-[var(--foreground-muted)] ml-1">Brand name</label>
              <DataInput 
                value={brandName} 
                onChange={(event) => setBrandName(event.target.value)} 
                placeholder="Your brand name" 
                aria-label="Brand name" 
                readOnly={true}
                required 
              />
            </div>
            <label className="block">
              <span className="mb-2 block text-sm font-bold text-[var(--foreground-muted)]">Plan tier</span>
              <select
                value={plan}
                onChange={(event) => setPlan(event.target.value as (typeof planOptions)[number]["value"])}
                className="machine-recessed h-14 w-full rounded-[var(--radius-md)] border-0 px-4 font-mono text-sm text-[var(--foreground)] focus:outline-none focus:shadow-[var(--shadow-recessed),0_0_0_2px_var(--accent)]"
              >
                {planOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <TactileButton type="submit" variant="primary" className="w-full justify-center" disabled={brandSubmitting}>
              {brandSubmitting ? "Onboarding brand..." : "Complete onboarding"}
            </TactileButton>
          </form>

          {brandMessage ? <div className="mt-4 rounded-[var(--radius-inner)] bg-[var(--bg-inner)] shadow-[inset_0_0_0_1px_rgba(255,255,255,0.1)] p-4 text-sm leading-6 text-[var(--foreground-muted)]">{brandMessage}</div> : null}

          {brandResult ? (
            <div className="mt-4 rounded-[var(--radius-inner)] border border-[rgba(34,197,94,0.2)] bg-[var(--status-success-bg)] p-4 text-sm text-[var(--status-success-text)]">
              <p className="font-bold">Brand onboarding complete!</p>
              <p className="mt-2">Brand: {brandResult.name}</p>
              <p>Plan: {brandResult.plan}</p>
              <p>Torch sub-account: {brandResult.torch_sub_id}</p>
            </div>
          ) : null}
        </Card>
      </div>

      <div className={`grid gap-6 ${isTorchproxyAdmin ? 'hidden' : 'max-w-2xl'}`}>
        <Card>
          <div className="flex items-start gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--background)] shadow-[var(--shadow-floating)]">
              <KeyRound className="h-7 w-7 text-[var(--accent)]" strokeWidth={1.8} />
            </div>
            <div>
              <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">Team management</p>
              <h3 className="mt-1 text-2xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">Add team members to your brand.</h3>
            </div>
          </div>

          <form className="mt-6 space-y-3" onSubmit={createUser}>
            <DataInput 
              value={brandId} 
              onChange={(event) => setBrandId(event.target.value)} 
              placeholder={`Brand ID (${currentSession.brand_id})`} 
              aria-label="Brand ID" 
              readOnly={true}
              required 
            />
            <DataInput value={fullName} onChange={(event) => setFullName(event.target.value)} placeholder="Full name" aria-label="Full name" required />
            <DataInput value={email} onChange={(event) => setEmail(event.target.value)} placeholder="Email" aria-label="Email" required />
            <DataInput value={password} onChange={(event) => setPassword(event.target.value)} type="password" placeholder="Password" aria-label="Password" required />
            <label className="block">
              <span className="mb-2 block text-sm font-bold text-[var(--foreground-muted)]">Role</span>
              <select
                value={role}
                onChange={(event) => setRole(event.target.value)}
                className="machine-recessed h-14 w-full rounded-[var(--radius-md)] border-0 px-4 font-mono text-sm text-[var(--foreground)] focus:outline-none focus:shadow-[var(--shadow-recessed),0_0_0_2px_var(--accent)]"
              >
                <option value="analyst">Analyst</option>
                <option value="admin">Admin</option>
              </select>
            </label>
            <TactileButton type="submit" variant="primary" className="w-full justify-center" disabled={userSubmitting}>
              {userSubmitting ? "Creating user..." : "Add team member"}
            </TactileButton>
          </form>

          {userMessage ? <div className="mt-4 rounded-[var(--radius-inner)] bg-[var(--bg-inner)] shadow-[inset_0_0_0_1px_rgba(255,255,255,0.1)] p-4 text-sm leading-6 text-[var(--foreground-muted)]">{userMessage}</div> : null}

          {userResult ? (
            <div className="mt-4 rounded-[var(--radius-inner)] border border-[rgba(34,197,94,0.2)] bg-[var(--status-success-bg)] p-4 text-sm text-[var(--status-success-text)]">
              <p className="font-bold">Team member added!</p>
              <p className="mt-2">Name: {userResult.full_name}</p>
              <p>Email: {userResult.email}</p>
              <p>Role: {userResult.role}</p>
              <p>Created: {formatDateTime(userResult.created_at)}</p>
            </div>
          ) : null}
        </Card>
      </div>
    </section>
  );
}
