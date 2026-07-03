"use client";

import { useRouter } from "next/navigation";
import { CheckCircle2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { TactileButton } from "@/components/ui/tactile-button";

export default function PendingPage() {
  const router = useRouter();

  return (
    <div className="relative min-h-screen overflow-hidden px-6 py-10 sm:px-8 lg:px-12 flex items-center justify-center">
      <div className="noise-layer" />
      <div className="grid-overlay" />

      <Card className="relative w-full max-w-lg text-center p-8 space-y-6">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-[var(--background)] shadow-[var(--shadow-floating)]">
          <CheckCircle2 className="h-8 w-8 text-[var(--status-success-text)]" strokeWidth={1.8} />
        </div>
        
        <div>
          <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">Registration Received</p>
          <h2 className="mt-2 text-3xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">Pending Approval</h2>
        </div>

        <p className="text-lg leading-7 text-[var(--foreground-muted)]">
          Thank you for registering your brand with VerifyShelf! Your application is currently under review by our proxy administration team.
        </p>

        <div className="rounded-[var(--radius-inner)] bg-[var(--bg-inner)] shadow-[inset_0_0_0_1px_rgba(255,255,255,0.1)] p-4 text-sm leading-6 text-[var(--foreground-muted)] text-left">
          <strong>What happens next?</strong>
          <ul className="mt-2 list-disc pl-5 space-y-1">
            <li>Our team will verify your company details.</li>
            <li>We may reach out if we need more information.</li>
            <li>Once approved, you will be notified via email.</li>
          </ul>
        </div>

        <TactileButton variant="secondary" onClick={() => router.push("/")} className="w-full justify-center">
          Return to Login
        </TactileButton>
      </Card>
    </div>
  );
}
