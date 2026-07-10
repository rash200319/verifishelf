"use client";

import { useRouter } from "next/navigation";
import { CheckCircle2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { TactileButton } from "@/components/ui/tactile-button";

export default function PendingPage() {
  const router = useRouter();

  return (
    <div className="flex min-h-screen items-center justify-center px-6 py-10 sm:px-8 lg:px-12">
      <Card className="w-full max-w-md text-center p-8 space-y-5">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[var(--status-success-bg)]">
          <CheckCircle2 className="h-6 w-6 text-[var(--status-success-text)]" strokeWidth={1.8} />
        </div>

        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--foreground-muted)]">Registration Received</p>
          <h2 className="mt-1.5 text-2xl font-semibold tracking-tight text-[var(--foreground)]">Pending Approval</h2>
        </div>

        <p className="text-base leading-6 text-[var(--foreground-muted)]">
          Thank you for registering your brand with VerifyShelf! Your application is currently under review by our proxy administration team.
        </p>

        <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--panel-muted)] p-4 text-sm leading-6 text-[var(--foreground-muted)] text-left">
          <strong className="text-[var(--foreground)]">What happens next?</strong>
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
