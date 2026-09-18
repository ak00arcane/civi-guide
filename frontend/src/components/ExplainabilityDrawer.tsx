"use client";

import React, { useEffect, useState } from "react";
import { reportScheme, SchemeItem } from "@/lib/api";

interface ExplainabilityDrawerProps {
  scheme: SchemeItem | null;
  onClose: () => void;
}

const TRUST_STYLES: Record<string, string> = {
  assertive: "bg-[var(--status-eligible-bg)] border-[var(--status-eligible-border)] text-[var(--status-eligible-text)]",
  hedged: "bg-[var(--status-likely-bg)] border-[var(--status-likely-border)] text-[var(--status-likely-text)]",
  discovery_only: "bg-[var(--status-not-bg)] border-[var(--status-not-border)] text-[var(--status-not-text)]",
};

const TRUST_LABELS: Record<string, string> = {
  assertive: "Verified",
  hedged: "Unconfirmed recently",
  discovery_only: "Could not confirm",
};

export const ExplainabilityDrawer: React.FC<ExplainabilityDrawerProps> = ({ scheme, onClose }) => {
  const [reportOpen, setReportOpen] = useState(false);
  const [reportText, setReportText] = useState("");
  const [reportState, setReportState] = useState<"idle" | "sending" | "sent" | "error">("idle");

  useEffect(() => {
    setReportOpen(false);
    setReportText("");
    setReportState("idle");
  }, [scheme?.id]);

  if (!scheme) return null;

  const passedTraces = scheme.traces?.filter((t) => t.result === "pass") || [];
  const unknownTraces = scheme.traces?.filter((t) => t.result === "unknown") || [];
  const failedTraces = scheme.traces?.filter((t) => t.result === "fail") || [];

  const submitReport = async () => {
    if (!reportText.trim()) return;
    setReportState("sending");
    try {
      await reportScheme(scheme.scheme_id, reportText.trim());
      setReportState("sent");
      setReportText("");
    } catch {
      setReportState("error");
    }
  };

  const traceGroups = [
    {
      list: passedTraces,
      label: "Satisfied criteria",
      icon: "✓",
      textClass: "text-[var(--status-eligible-text)]",
      boxClass: "bg-[var(--status-eligible-bg)] border-[var(--status-eligible-border)]",
    },
    {
      list: unknownTraces,
      label: "Information missing",
      icon: "?",
      textClass: "text-[var(--status-needs-text)]",
      boxClass: "bg-[var(--status-needs-bg)] border-[var(--status-needs-border)]",
    },
    {
      list: failedTraces,
      label: "Unmet criteria",
      icon: "✕",
      textClass: "text-[var(--status-not-text)]",
      boxClass: "bg-[var(--status-not-bg)] border-[var(--status-not-border)]",
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-stretch justify-end bg-slate-900/40 backdrop-blur-[2px]">
      <div className="w-full max-w-xl h-full bg-white border-l border-[var(--border-color)] shadow-[var(--shadow-lg)] overflow-y-auto flex flex-col">
        <div className="flex-1 px-6 py-6 space-y-5">
          {/* Header */}
          <div className="flex items-start justify-between border-b border-[var(--border-color)] pb-4">
            <div>
              <span className="text-xs font-bold uppercase tracking-wide text-[var(--primary)]">
                Recommendation audit
              </span>
              <h2 className="text-lg font-bold text-[var(--text-main)] mt-1">{scheme.scheme_name}</h2>
              <p className="text-xs text-[var(--text-muted)]">{scheme.category}</p>
            </div>
            <button onClick={onClose} className="btn btn-ghost w-8 h-8 p-0 text-sm shrink-0">
              ✕
            </button>
          </div>

          {/* Trust / source confidence */}
          {scheme.trust && (
            <div className={`rounded-xl p-4 space-y-1.5 border text-xs ${TRUST_STYLES[scheme.trust.claim_level] || TRUST_STYLES.hedged}`}>
              <div className="flex items-center justify-between">
                <span className="font-bold uppercase tracking-wide text-[10px]">
                  {TRUST_LABELS[scheme.trust.claim_level] || "Unconfirmed"}
                </span>
                {scheme.trust.confidence !== null && (
                  <span className="text-[10px] opacity-75">confidence {Math.round(scheme.trust.confidence * 100)}%</span>
                )}
              </div>
              <p>{scheme.trust.source_line}</p>
              {scheme.trust.qualifier && <p className="opacity-90">{scheme.trust.qualifier}</p>}
            </div>
          )}

          {/* Why matched */}
          {scheme.reasons && scheme.reasons.length > 0 && (
            <div className="bg-[var(--primary-soft-bg)] border border-[var(--primary-soft-border)] rounded-xl p-4 space-y-2">
              <h3 className="text-xs font-bold text-[var(--primary)] uppercase tracking-wide">Why you were matched</h3>
              <ul className="space-y-1.5 text-xs text-[var(--text-main)]">
                {scheme.reasons.map((r, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-[var(--primary)] font-bold">•</span>
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Why not eligible */}
          {scheme.why_not && scheme.why_not.length > 0 && (
            <div className="bg-[var(--status-not-bg)] border border-[var(--status-not-border)] rounded-xl p-4 space-y-2">
              <h3 className="text-xs font-bold text-[var(--status-not-text)] uppercase tracking-wide">
                Why you are not currently eligible
              </h3>
              <ul className="space-y-1.5 text-xs text-[var(--status-not-text)]">
                {scheme.why_not.map((wn, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="font-bold">✕</span>
                    <div>
                      <span className="font-semibold capitalize">{wn.rule_type.replace(/_/g, " ")}: </span>
                      <span>{wn.message}</span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Full rule trace breakdown */}
          <div className="space-y-4 pt-1">
            <h3 className="text-sm font-bold text-[var(--text-main)]">Full eligibility breakdown</h3>
            {traceGroups.map(
              (group) =>
                group.list.length > 0 && (
                  <div key={group.label} className="space-y-2">
                    <span className={`text-xs font-semibold flex items-center gap-1.5 ${group.textClass}`}>
                      <span>{group.icon}</span> {group.label} ({group.list.length})
                    </span>
                    <div className="space-y-1.5">
                      {group.list.map((t, idx) => (
                        <div key={idx} className={`rounded-lg p-2.5 text-xs border ${group.boxClass}`}>
                          <div className={`flex justify-between font-semibold ${group.textClass}`}>
                            <span className="capitalize">{t.rule_type.replace(/_/g, " ")}</span>
                            <span>{t.required ? "Required" : "Optional"}</span>
                          </div>
                          <p className="text-[var(--text-muted)] mt-1">{t.message}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )
            )}
          </div>
        </div>

        <div className="border-t border-[var(--border-color)] px-6 py-4 space-y-3">
          {reportState === "sent" ? (
            <p className="text-xs text-[var(--status-eligible-text)] text-center">Thanks — we'll take a look at this.</p>
          ) : reportOpen ? (
            <div className="space-y-2">
              <textarea
                value={reportText}
                onChange={(e) => setReportText(e.target.value)}
                placeholder="What looks wrong? e.g. the income limit or deadline is out of date."
                maxLength={1000}
                rows={3}
                className="field-input text-xs"
              />
              {reportState === "error" && (
                <p className="text-xs text-[var(--status-not-text)]">Couldn't submit that — please try again.</p>
              )}
              <div className="flex gap-2">
                <button
                  onClick={submitReport}
                  disabled={!reportText.trim() || reportState === "sending"}
                  className="btn btn-primary flex-1 text-xs py-2"
                >
                  {reportState === "sending" ? "Sending…" : "Submit report"}
                </button>
                <button onClick={() => setReportOpen(false)} className="btn btn-secondary text-xs py-2 px-3">
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <button onClick={() => setReportOpen(true)} className="btn btn-ghost w-full text-xs py-2 border border-[var(--border-color)]">
              ⚑ Report incorrect information
            </button>
          )}

          <button onClick={onClose} className="btn btn-secondary w-full text-xs py-2.5">
            Close explanation
          </button>
        </div>
      </div>
    </div>
  );
};
