"use client";

import React from "react";
import { OpportunityMapItem, ExploreOtherItem } from "@/lib/api";

interface OpportunityMapProps {
  opportunityMap: OpportunityMapItem[];
  exploreOther: ExploreOtherItem[];
  onSelectCategory?: (category: string) => void;
}

export const OpportunityMap: React.FC<OpportunityMapProps> = ({
  opportunityMap = [],
  exploreOther = [],
  onSelectCategory,
}) => {
  const maxCount = Math.max(...opportunityMap.map((o) => o.count), 1);

  return (
    <div className="space-y-6">
      {/* Category Density Chart */}
      <div className="card p-6 space-y-4">
        <div>
          <h3 className="text-base font-bold text-[var(--text-main)]">Scheme Density by Category</h3>
          <p className="text-xs text-[var(--text-muted)] mt-1">
            Matching government benefits across life categories, based on your query and eligibility profile.
          </p>
        </div>

        <div className="space-y-3 pt-1">
          {opportunityMap.length === 0 ? (
            <p className="text-xs text-[var(--text-dim)] italic">No opportunity data available for current selection.</p>
          ) : (
            opportunityMap.map((item, idx) => {
              const pct = Math.round((item.count / maxCount) * 100);
              return (
                <button
                  key={idx}
                  onClick={() => onSelectCategory && onSelectCategory(item.category)}
                  className="w-full text-left space-y-1.5 group"
                >
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-[var(--text-main)] group-hover:text-[var(--primary)] transition-colors">
                      {item.category}
                    </span>
                    <span className="text-[var(--primary)]">{item.count} schemes</span>
                  </div>
                  <div className="w-full h-2.5 bg-[var(--bg-subtle)] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[var(--primary)] rounded-full transition-all duration-500"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* Opportunity gaps */}
      {exploreOther.length > 0 && (
        <div className="card p-6 space-y-3">
          <div>
            <span className="text-xs font-bold uppercase tracking-wide text-[var(--primary)]">
              Opportunity gap analysis
            </span>
            <h3 className="text-sm font-bold text-[var(--text-main)] mt-0.5">
              Categories you might benefit from
            </h3>
            <p className="text-xs text-[var(--text-muted)] mt-1">
              Based on your profile, these additional benefit areas weren't named directly in your query:
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 pt-1">
            {exploreOther.map((item, idx) => (
              <div
                key={idx}
                className="bg-[var(--bg-subtle)] border border-[var(--border-color)] hover:border-[var(--primary-soft-border)] p-3.5 rounded-xl space-y-1.5 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-[var(--accent-teal)]" />
                  <span className="text-xs font-bold text-[var(--text-main)]">{item.label}</span>
                </div>
                {item.category && (
                  <span className="block text-[10px] text-[var(--text-dim)]">Target category: {item.category}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
