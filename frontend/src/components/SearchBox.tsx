"use client";

import React, { useState } from "react";

interface SearchBoxProps {
  onSearch: (query: string) => void;
  loading: boolean;
}

const SAMPLE_QUERIES = [
  "24-year-old student in Tamil Nadu needing financial help for education",
  "Unemployed graduate in Chennai looking for job & skill training",
  "Woman starting a small business in Tamil Nadu needing a startup grant",
  "62-year-old senior citizen looking for a healthcare pension",
  "Farmer in Punjab looking for irrigation and crop insurance support",
];

export const SearchBox: React.FC<SearchBoxProps> = ({ onSearch, loading }) => {
  const [query, setQuery] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  const handleChipClick = (sample: string) => {
    setQuery(sample);
    onSearch(sample);
  };

  return (
    <div className="w-full max-w-3xl mx-auto space-y-3">
      <form onSubmit={handleSubmit}>
        <div className="flex flex-col sm:flex-row items-stretch gap-2 card p-1.5">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Describe your situation in plain language…"
            className="flex-1 min-w-0 bg-transparent text-[var(--text-main)] placeholder-[var(--text-dim)] px-3.5 py-2.5 text-sm outline-none"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="btn btn-primary px-5 py-2.5 text-sm"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                <span>Analyzing…</span>
              </>
            ) : (
              <span>Find Schemes</span>
            )}
          </button>
        </div>
      </form>

      {/* Quick Example Prompt Chips */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-medium text-[var(--text-dim)]">Try:</span>
        {SAMPLE_QUERIES.map((sample, idx) => (
          <button
            key={idx}
            onClick={() => handleChipClick(sample)}
            disabled={loading}
            className="chip hover:border-[var(--primary-soft-border)] hover:bg-[var(--primary-soft-bg)] hover:text-[var(--primary-soft-text)] transition-colors max-w-[220px] truncate"
          >
            {sample}
          </button>
        ))}
      </div>
    </div>
  );
};
