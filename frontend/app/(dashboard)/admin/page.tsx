"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Building2, CheckCircle2, KeyRound, PlusCircle, ShieldCheck, UserPlus } from "lucide-react";
import { BoltedCard } from "@/components/ui/bolted-card";
import { DataInput } from "@/components/ui/data-input";
import { TactileButton } from "@/components/ui/tactile-button";
import { apiRequest } from "@/lib/api";
import type { BrandOnboardResponse, CreateUserResponse, SessionData } from "@/lib/backend-types";
import { clearSession, loadSession } from "@/lib/session";
import { formatDateTime } from "@/lib/format";

const planOptions = [
  { value: "starter", label: "Starter" },
  { value: "growth", label: "Growth" },
  { value: "enterprise", label: "Enterprise" },
] as const;

export default function AdminPage() {
  const router = useRouter();
  const [session, setSession] = useState<SessionData | null>(loadSession());
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

  useEffect(() => {
    const syncSession = () => setSession(loadSession());
    window.addEventListener("storage", syncSession);
    window.addEventListener("verifishelf-session", syncSession as EventListener);
    return () => {
      window.removeEventListener("storage", syncSession);
      window.removeEventListener("verifishelf-session", syncSession as EventListener);
    };
  }, []);

  useEffect(() => {
    if (!session) {
      router.replace("/");
      return;
    }

    if (session.role !== "admin") {
      router.replace("/dashboard");
    }
  }, [router, session]);

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
      const response = await apiRequest<BrandOnboardResponse>("/admin/brands/onboard", {
        method: "POST",
        session,
        body: JSON.stringify({ name: brandName, plan }),
      });

      setBrandResult(response.brand);
      setBrandId(String(response.brand.id));
      setBrandMessage(`Created brand ${response.brand.name} with Torch sub-account ${response.brand.torch_sub_id}.`);
      setBrandName("");
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
        <BoltedCard>
          <p className="monospace text-[0.7rem] font-bold uppercase tracking-[0.28em] text-[var(--foreground-muted)]">Access restricted</p>
          <h2 className="mt-2 text-3xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">TorchProxy onboarding is admin only.</h2>
          <p className="mt-3 max-w-2xl text-lg leading-8 text-[var(--foreground-muted)]">
            Sign in with the TorchProxy admin account to create brands and provision users.
          </p>
          <div className="mt-6">
            <TactileButton variant="primary" onClick={signOut}>
              Back to login
            </TactileButton>
          </div>
        </BoltedCard>
      </section>
    );
  }

  const currentSession = session;

  return (
    <section className="space-y-8 pb-10">
      <div className="max-w-4xl space-y-3">
        <p className="monospace text-[0.7rem] font-bold uppercase tracking-[0.28em] text-[var(--foreground-muted)]">TorchProxy console</p>
        <h2 className="text-4xl font-extrabold tracking-[-0.04em] text-[var(--foreground)] sm:text-5xl">Onboard brands and create their users.</h2>
        <p className="max-w-3xl text-lg leading-8 text-[var(--foreground-muted)]">
          This console is the only place where a new brand can be provisioned. Once the brand exists, TorchProxy adds the first users and hands the workspace off to them.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {[
          { icon: ShieldCheck, title: "Admin token", detail: `Signed in as ${currentSession.email ?? currentSession.brandName ?? currentSession.brand_name}` },
          { icon: Building2, title: "Brand onboarding", detail: "Creates the tenant and its Torch sub-account." },
          { icon: UserPlus, title: "User provisioning", detail: "Adds the first analyst or admin for that brand." },
        ].map((item) => (
          <BoltedCard key={item.title}>
            <item.icon className="h-6 w-6 text-[var(--accent)]" strokeWidth={1.8} />
            <p className="mt-3 text-sm font-bold text-[var(--foreground)]">{item.title}</p>
            <p className="mt-2 text-sm leading-6 text-[var(--foreground-muted)]">{item.detail}</p>
          </BoltedCard>
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <BoltedCard>
          <div className="flex items-start gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--background)] shadow-[var(--shadow-floating)]">
              <PlusCircle className="h-7 w-7 text-[var(--accent)]" strokeWidth={1.8} />
            </div>
            <div>
              <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">Brand onboarding</p>
              <h3 className="mt-1 text-2xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">Create a brand and its Torch sub-account.</h3>
            </div>
          </div>

          <form className="mt-6 space-y-3" onSubmit={onboardBrand}>
            <DataInput value={brandName} onChange={(event) => setBrandName(event.target.value)} placeholder="Brand name" aria-label="Brand name" required />
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
              {brandSubmitting ? "Creating brand..." : "Create brand"}
            </TactileButton>
          </form>

          {brandMessage ? <div className="mt-4 rounded-[18px] bg-[rgba(255,255,255,0.62)] p-4 text-sm leading-6 text-[var(--foreground-muted)]">{brandMessage}</div> : null}

          {brandResult ? (
            <div className="mt-4 rounded-[18px] border border-[rgba(255,71,87,0.15)] bg-[rgba(255,71,87,0.06)] p-4 text-sm text-[var(--foreground)]">
              <p className="font-bold">Latest brand</p>
              <p className="mt-2">ID: {brandResult.id}</p>
              <p>Plan: {brandResult.plan}</p>
              <p>Torch sub-account: {brandResult.torch_sub_id}</p>
              <p>Created: {formatDateTime(brandResult.created_at)}</p>
            </div>
          ) : null}
        </BoltedCard>

        <BoltedCard>
          <div className="flex items-start gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--background)] shadow-[var(--shadow-floating)]">
              <KeyRound className="h-7 w-7 text-[var(--accent)]" strokeWidth={1.8} />
            </div>
            <div>
              <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">User provisioning</p>
              <h3 className="mt-1 text-2xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">Create the first user for a brand.</h3>
            </div>
          </div>

          <form className="mt-6 space-y-3" onSubmit={createUser}>
            <DataInput value={brandId} onChange={(event) => setBrandId(event.target.value)} placeholder="Brand ID" aria-label="Brand ID" required />
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
              {userSubmitting ? "Creating user..." : "Create user"}
            </TactileButton>
          </form>

          {userMessage ? <div className="mt-4 rounded-[18px] bg-[rgba(255,255,255,0.62)] p-4 text-sm leading-6 text-[var(--foreground-muted)]">{userMessage}</div> : null}

          {userResult ? (
            <div className="mt-4 rounded-[18px] border border-[rgba(34,197,94,0.15)] bg-[rgba(34,197,94,0.06)] p-4 text-sm text-[var(--foreground)]">
              <p className="font-bold">Latest user</p>
              <p className="mt-2">Name: {userResult.full_name}</p>
              <p>Email: {userResult.email}</p>
              <p>Brand ID: {userResult.brand_id}</p>
              <p>Role: {userResult.role}</p>
              <p>Created: {formatDateTime(userResult.created_at)}</p>
            </div>
          ) : null}
        </BoltedCard>
      </div>
    </section>
  );
}
