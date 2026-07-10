"use client";

import { useEffect, useState } from "react";
import { Copy, PlusCircle, Check, Users } from "lucide-react";
import { Card } from "@/components/ui/card";
import { DataInput } from "@/components/ui/data-input";
import { Select } from "@/components/ui/select";
import { TactileButton } from "@/components/ui/tactile-button";
import { apiRequest } from "@/lib/api";
import { loadSession } from "@/lib/session";
import { formatDateTime } from "@/lib/format";
import type { SessionData } from "@/lib/backend-types";

interface Invite {
  id: number;
  email: string | null;
  role: string;
  expires_at: string;
  used_at: string | null;
  created_at: string;
}

export default function InvitesPage() {
  const [session] = useState<SessionData | null>(loadSession());
  const [invites, setInvites] = useState<Invite[]>([]);
  const [loading, setLoading] = useState(true);

  const [email, setEmail] = useState("");
  const [role, setRole] = useState("analyst");
  const [expiresIn, setExpiresIn] = useState("10080"); // 7 days
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [newInviteLink, setNewInviteLink] = useState("");
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchInvites();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchInvites = async () => {
    if (!session) return;
    try {
      setLoading(true);
      const res = await apiRequest<{ invites: Invite[] }>("/brands/invites", { session });
      setInvites(res.invites || []);
    } catch (err) {
      console.error("Failed to fetch invites", err);
    } finally {
      setLoading(false);
    }
  };

  const submitInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!session) return;
    setIsSubmitting(true);
    setError("");
    setNewInviteLink("");
    setCopied(false);

    try {
      const res = await apiRequest<{ message: string, invite: Invite & { invite_code: string } }>("/brands/invites", {
        method: "POST",
        session,
        body: JSON.stringify({
          email: email.trim() ? email.trim() : null,
          role,
          expires_in_minutes: parseInt(expiresIn, 10),
        }),
      });

      const inviteLink = `${window.location.origin}/join?code=${res.invite.invite_code}`;
      setNewInviteLink(inviteLink);
      setEmail("");
      fetchInvites();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create invite");
    } finally {
      setIsSubmitting(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(newInviteLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!session || session.role !== "admin") {
    return (
      <Card className="p-8 text-center">
        <h2 className="text-xl font-semibold text-[var(--foreground)]">Access Denied</h2>
        <p className="mt-2 text-[var(--foreground-muted)]">Only brand admins can manage invites.</p>
      </Card>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-[var(--foreground-muted)]">Workspace Settings</p>
        <h2 className="mt-1.5 text-3xl font-semibold tracking-tight text-[var(--foreground)]">Manage Invites</h2>
        <p className="mt-2 text-base text-[var(--foreground-muted)] max-w-2xl">
          Invite new members to your brand workspace. They will be able to monitor MAP compliance and review reports.
        </p>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_2fr]">
        {/* Create Invite Form */}
        <Card className="h-fit">
          <div className="flex items-start gap-3 mb-5">
            <div className="flex h-10 w-10 items-center justify-center rounded-[var(--radius-lg)] bg-[var(--accent-soft)]">
              <PlusCircle className="h-5 w-5 text-[var(--accent)]" />
            </div>
            <div>
              <h3 className="text-lg font-semibold tracking-tight text-[var(--foreground)]">New Invite</h3>
              <p className="text-xs text-[var(--foreground-muted)]">Generate a secure access link</p>
            </div>
          </div>

          <form onSubmit={submitInvite} className="space-y-3.5">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-[var(--foreground-muted)]">Email Address (optional)</label>
              <DataInput
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="colleague@company.com"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-[var(--foreground-muted)]">Role</label>
              <Select value={role} onChange={(e) => setRole(e.target.value)}>
                <option value="analyst">Analyst (Read-only + Promos)</option>
                <option value="admin">Admin (Full Access)</option>
              </Select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-[var(--foreground-muted)]">Expiration</label>
              <Select value={expiresIn} onChange={(e) => setExpiresIn(e.target.value)}>
                <option value="60">1 Hour</option>
                <option value="1440">24 Hours</option>
                <option value="10080">7 Days</option>
                <option value="43200">30 Days</option>
              </Select>
            </div>

            <TactileButton type="submit" variant="primary" className="w-full justify-center" disabled={isSubmitting}>
              {isSubmitting ? "Generating..." : "Generate Link"}
            </TactileButton>
          </form>

          {error && (
            <div className="mt-4 p-3 rounded-[var(--radius-md)] bg-[var(--status-error-bg)] text-[var(--status-error-text)] text-sm">
              {error}
            </div>
          )}

          {newInviteLink && (
            <div className="mt-5 p-4 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--panel-muted)]">
              <p className="text-xs font-semibold text-[var(--status-success-text)] mb-2 flex items-center gap-1">
                <Check className="h-3 w-3" /> Invite Generated
              </p>
              <div className="flex gap-2">
                <input
                  readOnly
                  value={newInviteLink}
                  className="flex-1 bg-transparent text-xs text-[var(--foreground)] truncate outline-none"
                />
                <button
                  onClick={copyToClipboard}
                  className="p-1.5 rounded-[var(--radius-sm)] hover:bg-[var(--panel)] text-[var(--foreground-muted)] transition-colors"
                  title="Copy link"
                >
                  {copied ? <Check className="h-4 w-4 text-[var(--status-success-text)]" /> : <Copy className="h-4 w-4" />}
                </button>
              </div>
            </div>
          )}
        </Card>

        {/* Invites List */}
        <Card>
          <div className="flex items-start gap-3 mb-5">
            <div className="flex h-10 w-10 items-center justify-center rounded-[var(--radius-lg)] bg-[var(--accent-soft)]">
              <Users className="h-5 w-5 text-[var(--accent)]" />
            </div>
            <div>
              <h3 className="text-lg font-semibold tracking-tight text-[var(--foreground)]">Active & Past Invites</h3>
              <p className="text-xs text-[var(--foreground-muted)]">History of generated links</p>
            </div>
          </div>

          {loading ? (
            <p className="text-sm text-[var(--foreground-muted)]">Loading invites...</p>
          ) : invites.length === 0 ? (
            <div className="py-8 text-center text-[var(--foreground-muted)] border border-dashed border-[var(--border)] rounded-[var(--radius-md)]">
              No invites have been generated yet.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-[var(--border)] text-[var(--foreground-muted)]">
                    <th className="pb-3 font-medium">Target Email</th>
                    <th className="pb-3 font-medium">Role</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 font-medium">Expires</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border)]">
                  {invites.map((invite) => {
                    const isExpired = new Date(invite.expires_at) < new Date();
                    const isUsed = !!invite.used_at;

                    let statusLabel = "Pending";
                    let statusColor = "text-[var(--status-warning-text)]";

                    if (isUsed) {
                      statusLabel = "Accepted";
                      statusColor = "text-[var(--status-success-text)]";
                    } else if (isExpired) {
                      statusLabel = "Expired";
                      statusColor = "text-[var(--status-error-text)]";
                    }

                    return (
                      <tr key={invite.id}>
                        <td className="py-3 text-[var(--foreground)]">{invite.email || <span className="text-[var(--foreground-muted)] italic">Any</span>}</td>
                        <td className="py-3 capitalize text-[var(--foreground)]">{invite.role}</td>
                        <td className={`py-3 font-medium ${statusColor}`}>{statusLabel}</td>
                        <td className="py-3 text-[var(--foreground-muted)]">
                          {formatDateTime(invite.expires_at)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
