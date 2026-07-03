"use client";

import { useEffect, useState } from "react";
import { TriangleAlert } from "lucide-react";

const incidents = [
  { marketplace: "Daraz PK", label: "MAP violation", delta: "-18.4%", severity: "warning", width: "65%" },
  { marketplace: "Shopee ID", label: "Grey market", delta: "-9.2%", severity: "warning", width: "80%" },
  { marketplace: "Tokopedia", label: "Compliant", delta: "0.0%", severity: "compliant", width: "100%" },
  { marketplace: "Flipkart", label: "Counterfeit risk", delta: "-31.7%", severity: "severe", width: "35%" },
  { marketplace: "Lazada SG", label: "MAP violation", delta: "-14.2%", severity: "warning", width: "70%" },
  { marketplace: "Amazon IN", label: "Counterfeit risk", delta: "-42.5%", severity: "severe", width: "20%" },
];

export function DashboardPreview() {
  const [isHovered, setIsHovered] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const doubleIncidents = [...incidents, ...incidents];

  if (!mounted) {
    return (
      <div className="grid gap-4 md:grid-cols-[1.1fr_0.9fr] min-h-[380px]" />
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-[1.1fr_0.9fr]">
      {/* Left Column - Live Feed Ticker */}
      <div className="space-y-4 rounded-[20px] bg-[rgba(9,13,17,0.72)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.06)] flex flex-col h-[380px]">
        <div className="flex items-center justify-between text-[0.64rem] font-bold uppercase tracking-[0.24em] text-[rgba(232,238,244,0.65)] shrink-0">
          <span>Live feed</span>
          <span className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#22c55e] opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#22c55e]" />
            </span>
            18 listings / minute
          </span>
        </div>

        {/* Ticker Window */}
        <div 
          className="relative flex-1 overflow-hidden [mask-image:linear-gradient(to_bottom,transparent_0%,white_15%,white_85%,transparent_100%)] cursor-pointer"
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
        >
          <div
            className="space-y-3 py-2 animate-ticker"
            style={{
              animationPlayState: isHovered ? "paused" : "running",
            }}
          >
            {doubleIncidents.map((item, idx) => {
              const deltaColor =
                item.severity === "severe"
                  ? "text-[#ff8b94]"
                  : item.severity === "warning"
                    ? "text-[#fde68a]"
                    : "text-[#86efac]";
              const barColor =
                item.severity === "severe"
                  ? "bg-[#ff4757]"
                  : item.severity === "warning"
                    ? "bg-[#f59e0b]"
                    : "bg-[#22c55e]";

              return (
                <div
                  key={`${item.marketplace}-${idx}`}
                  className="rounded-[18px] bg-[rgba(255,255,255,0.05)] p-3 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.06)] hover:bg-[rgba(255,255,255,0.08)] transition-colors duration-150"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 text-sm font-bold text-white">
                    <span>{item.marketplace}</span>
                    <span className={`monospace shrink-0 ${deltaColor}`}>{item.delta}</span>
                  </div>
                  <p className="mt-1.5 text-[0.72rem] uppercase tracking-[0.18em] text-[rgba(232,238,244,0.55)]">
                    {item.label}
                  </p>
                  <div className="mt-2.5 h-1.5 rounded-full bg-[rgba(255,255,255,0.08)]">
                    <div
                      className={`h-1.5 rounded-full ${barColor}`}
                      style={{ width: item.width }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Right Column - Status & Packet */}
      <div className="space-y-4 rounded-[20px] bg-[rgba(255,255,255,0.04)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.05)] flex flex-col justify-between h-[380px] shrink-0">
        <div className="space-y-4">
          <div className="flex items-center justify-between text-[0.64rem] font-bold uppercase tracking-[0.24em] text-[rgba(232,238,244,0.64)]">
            <span>Pipeline status</span>
            <span className="monospace text-[#93c5fd]">&lt; 500ms</span>
          </div>
          <div className="space-y-2.5">
            {[
              ["Proxy routing", "online"],
              ["Playwright extraction", "active"],
              ["XGBoost scoring", "active"],
              ["GPT-4o draft queue", "ready"],
            ].map(([label, state]) => (
              <div key={label} className="flex items-center justify-between rounded-[16px] bg-[rgba(9,13,17,0.7)] px-3 py-2 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.05)]">
                <span className="text-sm font-medium text-white">{label}</span>
                <span className="monospace rounded-full border border-[rgba(34,197,94,0.4)] bg-[rgba(34,197,94,0.06)] px-2.5 py-0.5 text-[0.65rem] font-bold uppercase tracking-[0.18em] text-[#86efac]">
                  {state}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-[20px] bg-[rgba(255,255,255,0.06)] p-3.5 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.05)]">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 shrink-0 rounded-full bg-[rgba(255,71,87,0.12)] shadow-[inset_0_0_0_1px_rgba(255,71,87,0.22)]">
              <TriangleAlert className="m-2 h-6 w-6 text-[#ff8b94]" />
            </div>
            <div className="min-w-0">
              <p className="text-xs font-bold text-white truncate">Latest enforcement packet</p>
              <p className="text-[0.68rem] text-[rgba(232,238,244,0.62)] truncate">1 C&D draft, 2 screenshots, 3 citations</p>
            </div>
          </div>
          <div className="mt-3 grid grid-cols-3 gap-2 text-center text-[0.6rem] font-bold uppercase tracking-[0.18em] text-[rgba(232,238,244,0.64)]">
            <div className="rounded-[10px] bg-[rgba(255,255,255,0.05)] p-1.5 hover:bg-[rgba(255,255,255,0.1)] transition-colors cursor-pointer">Evidence</div>
            <div className="rounded-[10px] bg-[rgba(255,255,255,0.05)] p-1.5 hover:bg-[rgba(255,255,255,0.1)] transition-colors cursor-pointer">Review</div>
            <div className="rounded-[10px] bg-[rgba(255,255,255,0.05)] p-1.5 hover:bg-[rgba(255,255,255,0.1)] transition-colors cursor-pointer">Send</div>
          </div>
        </div>
      </div>
    </div>
  );
}
