"use client";

import React from "react";
import { SavedSchemeItem, SchemeItem } from "@/lib/api";
import { SchemeCard } from "./SchemeCard";

interface SavedSchemesViewProps {
  savedItems: SavedSchemeItem[];
  allSchemes: SchemeItem[];
  onOpenExplain: (scheme: SchemeItem) => void;
  onSaveScheme: (schemeId: string, status: string) => void;
  note?: string;
}

export const SavedSchemesView: React.FC<SavedSchemesViewProps> = ({
  savedItems = [],
  allSchemes = [],
  onOpenExplain,
  onSaveScheme,
  note = "Personal reminder — not official application tracking.",
}) => {
  const savedMap = new Map(savedItems.map((s) => [s.scheme_id, s.personal_status]));
  const matchingSchemes = allSchemes.filter((sc) => savedMap.has(sc.scheme_id));

  return (
    <div className="space-y-6">
      <div className="card p-6 space-y-2">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-[var(--text-main)]">Your Bookmarked Schemes</h2>
          <span className="chip">{savedItems.length} saved</span>
        </div>
        <p className="text-xs text-[var(--text-muted)]">ℹ️ {note}</p>
      </div>

      {matchingSchemes.length === 0 ? (
        <div className="card p-12 text-center space-y-3">
          <span className="text-4xl block">🔖</span>
          <h3 className="text-sm font-bold text-[var(--text-main)]">No schemes bookmarked yet</h3>
          <p className="text-xs text-[var(--text-muted)] max-w-sm mx-auto">
            Click the bookmark icon on any scheme recommendation card to set application reminders.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {matchingSchemes.map((scheme) => (
            <SchemeCard
              key={scheme.scheme_id}
              scheme={scheme}
              onOpenExplain={onOpenExplain}
              onSaveScheme={onSaveScheme}
              savedStatus={savedMap.get(scheme.scheme_id)}
            />
          ))}
        </div>
      )}
    </div>
  );
};
