"use client";

import React, { useState } from "react";
import { SchemeItem } from "@/lib/api";

interface SchemeCardProps {
  scheme: SchemeItem;
  rank?: number;
  onOpenExplain: (scheme: SchemeItem) => void;
  onSaveScheme: (schemeId: string, status: string) => void;
  savedStatus?: string | null;
}

const BADGE_MAP: Record<string, { label: string; className: string }> = {
  eligible: { label: "Eligible", className: "badge-eligible" },
  likely_eligible: { label: "Likely Eligible", className: "badge-likely" },
  needs_more_information: { label: "Needs Info", className: "badge-needs" },
  not_eligible: { label: "Not Eligible", className: "badge-not" },
};

export const SchemeCard: React.FC<SchemeCardProps> = ({
  scheme,
  rank,
  onOpenExplain,
  onSaveScheme,
  savedStatus,
}) => {
  const [showStatusSelect, setShowStatusSelect] = useState(false);

  const badge = BADGE_MAP[scheme.eligibility_status] || BADGE_MAP.needs_more_information;
  const officialUrl = scheme.sources?.find((s) => s.official_application_url)?.official_application_url;

  return (
    <div className="card card-hover p-5 flex flex-col justify-between">
      <div className="space-y-3">
        {/* Status row */}
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            {rank && (
              <span className="w-5 h-5 rounded-md bg-[var(--bg-subtle)] text-[var(--text-muted)] text-[11px] font-bold flex items-center justify-center">
                {rank}
              </span>
            )}
            <span className={`badge ${badge.className}`}>{badge.label}</span>
          </div>
          <span className="text-xs font-semibold text-[var(--text-dim)]">
            {Math.round(scheme.score * 100)}% match
          </span>
        </div>

        {/* Demo banner indicator */}
        {scheme.is_demo && (
          <div className="text-[11px] font-medium text-amber-700 bg-amber-50 border border-amber-200 px-2.5 py-1 rounded-lg">
            ⚠️ {scheme.demo_banner || "Demo data — replace with verified official scheme information."}
          </div>
        )}

        {/* Title & Description */}
        <div>
          <h3 className="text-base font-bold text-[var(--text-main)] leading-snug">
            {scheme.scheme_name}
          </h3>
          <p className="text-xs text-[var(--text-muted)] mt-1 line-clamp-2 leading-relaxed">
            {scheme.description}
          </p>
        </div>

        {/* Meta chips */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="chip">{scheme.category}</span>
          {scheme.government_level && (
            <span className="chip">
              {scheme.government_level === "central" ? "Central government" : "State government"}
            </span>
          )}
          {scheme.state && <span className="chip">📍 {scheme.state}</span>}
        </div>

        {/* Key Benefit */}
        {scheme.benefits_summary && (
          <div className="bg-[var(--accent-teal-soft-bg)] border border-[var(--border-color)] rounded-xl px-3 py-2.5">
            <span className="text-[10px] font-bold text-[var(--accent-teal-hover)] uppercase tracking-wide block mb-0.5">
              Benefit
            </span>
            <p className="text-xs font-semibold text-[var(--text-main)]">{scheme.benefits_summary}</p>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="pt-3.5 mt-3.5 border-t border-[var(--border-color)] flex items-center justify-between gap-2">
        <button
          onClick={() => onOpenExplain(scheme)}
          className="text-xs font-semibold text-[var(--primary)] hover:text-[var(--primary-hover)] underline underline-offset-4 decoration-[var(--primary-soft-border)]"
        >
          Why this recommendation?
        </button>

        <div className="flex items-center gap-2">
          {/* Bookmark / Reminder Toggle */}
          <div className="relative">
            <button
              onClick={() => setShowStatusSelect(!showStatusSelect)}
              title={savedStatus ? savedStatus.replace("_", " ") : "Save"}
              className={`w-8 h-8 rounded-lg text-sm flex items-center justify-center border transition-colors ${
                savedStatus
                  ? "bg-[var(--primary-soft-bg)] border-[var(--primary-soft-border)]"
                  : "bg-white border-[var(--border-strong)] hover:bg-[var(--bg-subtle)]"
              }`}
            >
              🔖
            </button>

            {showStatusSelect && (
              <div className="absolute right-0 bottom-full mb-2 w-48 card p-1.5 space-y-0.5 z-20 shadow-[var(--shadow-lg)]">
                {[
                  { id: "saved", label: "Save for later" },
                  { id: "need_to_apply", label: "Need to apply" },
                  { id: "applied_reminder", label: "Applied (reminder)" },
                ].map((st) => (
                  <button
                    key={st.id}
                    onClick={() => {
                      onSaveScheme(scheme.scheme_id, st.id);
                      setShowStatusSelect(false);
                    }}
                    className="w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-medium text-[var(--text-main)] hover:bg-[var(--primary-soft-bg)] hover:text-[var(--primary)] transition-colors"
                  >
                    {st.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Official Apply URL button */}
          {officialUrl ? (
            <a href={officialUrl} target="_blank" rel="noopener noreferrer" className="btn btn-accent text-xs px-3.5 py-1.5">
              Apply <span aria-hidden>↗</span>
            </a>
          ) : (
            <span className="text-[10px] text-[var(--text-dim)] italic">No official link</span>
          )}
        </div>
      </div>
    </div>
  );
};
