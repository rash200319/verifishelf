"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Building2, FileText, Globe, User } from "lucide-react";
import { Card } from "@/components/ui/card";
import { DataInput } from "@/components/ui/data-input";
import { Select } from "@/components/ui/select";
import { TactileButton } from "@/components/ui/tactile-button";
import { apiRequest } from "@/lib/api";

const industryOptions = [
  "Consumer Electronics",
  "Apparel & Fashion",
  "Cosmetics & Beauty",
  "Home & Living",
  "Health & Wellness",
  "Sporting Goods",
  "Baby & Kids",
  "Other",
];

const skuRangeOptions = ["1-20", "21-100", "101-500", "500+"];

const marketplaceOptions = ["Daraz", "Amazon", "Flipkart", "Lazada", "Tokopedia", "Other"];

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [brandName, setBrandName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [businessUrl, setBusinessUrl] = useState("");
  const [notes, setNotes] = useState("");

  // Brand application / KYB fields -- this product drafts enforcement
  // letters in the brand's name, so a superadmin reviewing this needs more
  // than just a name and a URL to judge whether the applicant is real and
  // authorized to act for this brand.
  const [registrationNumber, setRegistrationNumber] = useState("");
  const [businessAddress, setBusinessAddress] = useState("");
  const [industry, setIndustry] = useState(industryOptions[0]);
  const [contactTitle, setContactTitle] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const [estimatedSkuRange, setEstimatedSkuRange] = useState(skuRangeOptions[0]);
  const [currentMarketplaces, setCurrentMarketplaces] = useState<string[]>([]);
  const [authorizedAttestation, setAuthorizedAttestation] = useState(false);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const toggleMarketplace = (marketplace: string) => {
    setCurrentMarketplaces((prev) =>
      prev.includes(marketplace) ? prev.filter((m) => m !== marketplace) : [...prev, marketplace],
    );
  };

  const submitRegister = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError("");

    if (currentMarketplaces.length === 0) {
      setError("Select at least one marketplace you currently sell on.");
      setIsSubmitting(false);
      return;
    }

    if (!authorizedAttestation) {
      setError("You must confirm you are authorized to submit MAP enforcement actions on behalf of this brand.");
      setIsSubmitting(false);
      return;
    }

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
          registration_number: registrationNumber,
          business_address: businessAddress,
          industry,
          contact_title: contactTitle,
          contact_phone: contactPhone,
          estimated_sku_range: estimatedSkuRange,
          current_marketplaces: currentMarketplaces,
          authorized_attestation: authorizedAttestation,
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
    <div className="min-h-screen px-6 py-10 sm:px-8 lg:px-12">
      <div className="mx-auto grid min-h-[calc(100vh-5rem)] max-w-6xl gap-10 lg:grid-cols-[1fr_0.9fr] lg:items-center">
        <div className="space-y-8">
          <div className="inline-flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--panel)] px-3 py-1.5 text-xs font-medium text-[var(--foreground-muted)]">
            <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent)]" />
            VerifyShelf brand onboarding
          </div>

          <div className="space-y-4">
            <h1 className="max-w-xl text-4xl font-semibold tracking-tight text-[var(--foreground)] sm:text-5xl">
              Register your brand to start enforcing MAP policies.
            </h1>
            <p className="max-w-lg text-lg leading-7 text-[var(--foreground-muted)]">
              Join VerifyShelf to protect your margins, monitor unauthorized sellers, and enforce MAP guidelines automatically.
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
                <item.icon className="h-5 w-5 text-[var(--accent)]" strokeWidth={1.8} />
                <p className="mt-3 text-sm font-semibold text-[var(--foreground)]">{item.title}</p>
                <p className="mt-1.5 text-sm leading-5 text-[var(--foreground-muted)]">{item.detail}</p>
              </Card>
            ))}
          </div>
        </div>

        <Card className="mx-auto w-full max-w-md">
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--foreground-muted)]">Sign up</p>
          <h2 className="mt-1.5 text-2xl font-semibold tracking-tight text-[var(--foreground)]">Create your workspace.</h2>

          <form className="mt-6 space-y-4" onSubmit={submitRegister}>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5 text-left">
                <label className="text-xs font-medium text-[var(--foreground-muted)]">Full Name</label>
                <DataInput value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Full name" required />
              </div>
              <div className="space-y-1.5 text-left">
                <label className="text-xs font-medium text-[var(--foreground-muted)]">Email Address</label>
                <DataInput type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email address" required />
              </div>
            </div>

            <div className="space-y-1.5 text-left">
              <label className="text-xs font-medium text-[var(--foreground-muted)]">Password</label>
              <DataInput type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" required />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5 text-left">
                <label className="text-xs font-medium text-[var(--foreground-muted)]">Brand Name</label>
                <DataInput value={brandName} onChange={(e) => setBrandName(e.target.value)} placeholder="Main brand name" required />
              </div>
              <div className="space-y-1.5 text-left">
                <label className="text-xs font-medium text-[var(--foreground-muted)]">Company Name</label>
                <DataInput value={companyName} onChange={(e) => setCompanyName(e.target.value)} placeholder="Legal entity" required />
              </div>
            </div>

            <div className="space-y-1.5 text-left">
              <label className="text-xs font-medium text-[var(--foreground-muted)]">Business URL</label>
              <DataInput value={businessUrl} onChange={(e) => setBusinessUrl(e.target.value)} placeholder="https://..." required />
            </div>

            <p className="pt-2 text-xs font-semibold uppercase tracking-wide text-[var(--foreground-muted)]">Business verification</p>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5 text-left">
                <label className="text-xs font-medium text-[var(--foreground-muted)]">Business Registration Number</label>
                <DataInput value={registrationNumber} onChange={(e) => setRegistrationNumber(e.target.value)} placeholder="Company reg. / incorporation no." required />
              </div>
              <div className="space-y-1.5 text-left">
                <label className="text-xs font-medium text-[var(--foreground-muted)]">Industry</label>
                <Select value={industry} onChange={(e) => setIndustry(e.target.value)}>
                  {industryOptions.map((option) => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </Select>
              </div>
            </div>

            <div className="space-y-1.5 text-left">
              <label className="text-xs font-medium text-[var(--foreground-muted)]">Registered Business Address</label>
              <DataInput value={businessAddress} onChange={(e) => setBusinessAddress(e.target.value)} placeholder="Street, city, country" required />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5 text-left">
                <label className="text-xs font-medium text-[var(--foreground-muted)]">Your Title / Role</label>
                <DataInput value={contactTitle} onChange={(e) => setContactTitle(e.target.value)} placeholder="e.g. Brand Manager" required />
              </div>
              <div className="space-y-1.5 text-left">
                <label className="text-xs font-medium text-[var(--foreground-muted)]">Contact Phone</label>
                <DataInput value={contactPhone} onChange={(e) => setContactPhone(e.target.value)} placeholder="+1 555 000 0000" required />
              </div>
            </div>

            <div className="space-y-1.5 text-left">
              <label className="text-xs font-medium text-[var(--foreground-muted)]">Estimated SKU Count</label>
              <Select value={estimatedSkuRange} onChange={(e) => setEstimatedSkuRange(e.target.value)}>
                {skuRangeOptions.map((option) => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </Select>
            </div>

            <div className="space-y-1.5 text-left">
              <label className="text-xs font-medium text-[var(--foreground-muted)]">Marketplaces You Currently Sell On</label>
              <div className="grid grid-cols-2 gap-2 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--panel-muted)] p-3 sm:grid-cols-3">
                {marketplaceOptions.map((marketplace) => (
                  <label key={marketplace} className="flex items-center gap-2 text-sm text-[var(--foreground)]">
                    <input
                      type="checkbox"
                      checked={currentMarketplaces.includes(marketplace)}
                      onChange={() => toggleMarketplace(marketplace)}
                      className="h-4 w-4 rounded border-[var(--border-strong)] text-[var(--accent)]"
                    />
                    {marketplace}
                  </label>
                ))}
              </div>
            </div>

            <div className="space-y-1.5 text-left">
              <label className="text-xs font-medium text-[var(--foreground-muted)]">Additional Notes</label>
              <DataInput value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="How did you hear about us? Any specific needs?" />
            </div>

            <label className="flex items-start gap-3 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--panel-muted)] p-3 text-sm leading-6 text-[var(--foreground)]">
              <input
                type="checkbox"
                checked={authorizedAttestation}
                onChange={(e) => setAuthorizedAttestation(e.target.checked)}
                className="mt-1 h-4 w-4 shrink-0 rounded border-[var(--border-strong)] text-[var(--accent)]"
                required
              />
              <span>
                I confirm that I am authorized to submit MAP enforcement actions (including takedown/cease-and-desist requests) on behalf of this brand.
              </span>
            </label>

            <TactileButton type="submit" variant="primary" className="w-full justify-center" disabled={isSubmitting}>
              {isSubmitting ? "Submitting..." : "Submit Registration"}
            </TactileButton>
          </form>

          {error ? (
            <div className="mt-4 rounded-[var(--radius-md)] bg-[var(--status-error-bg)] px-4 py-3 text-sm text-[var(--status-error-text)]">
              {error}
            </div>
          ) : null}

          <div className="mt-6 text-center space-y-2">
            <p className="text-xs text-[var(--foreground-muted)]">
              Already have an account?{" "}
              <a href="/" onClick={(e) => { e.preventDefault(); router.push("/"); }} className="underline hover:text-[var(--accent)] transition-colors">
                Sign in here
              </a>
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
}
