"use client";

import React from "react";

type Tab = "results" | "grouped" | "opportunity" | "saved";

interface HeaderProps {
  activeTab: Tab;
  setActiveTab: (tab: Tab) => void;
  savedCount: number;
  onOpenProfile: () => void;
  hasProfile: boolean;
}

const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: "results", label: "Recommendations", icon: "🎯" },
  { id: "grouped", label: "By Category", icon: "🗂️" },
  { id: "opportunity", label: "Opportunity Map", icon: "🧭" },
  { id: "saved", label: "Saved", icon: "🔖" },
];

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  savedCount,
  onOpenProfile,
  hasProfile,
}) => {
  return (
    <>
      <header className="sticky top-0 z-40 bg-white/90 backdrop-blur-sm border-b border-[var(--border-color)] px-4 lg:px-8 py-3 flex items-center justify-between">
        {/* Logo / Title */}
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[var(--primary)] flex items-center justify-center text-white font-bold text-base">
            C
          </div>
          <span className="text-lg font-bold text-[var(--text-main)] tracking-tight">CivicGuide</span>
          <span className="hidden sm:inline chip">India MVP</span>
        </div>

        {/* Navigation Tabs (desktop) */}
        <nav className="hidden md:flex items-center gap-1">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`relative px-3.5 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 ${
                activeTab === tab.id
                  ? "text-[var(--primary)] bg-[var(--primary-soft-bg)]"
                  : "text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--bg-subtle)]"
              }`}
            >
              <span>{tab.label}</span>
              {tab.id === "saved" && savedCount > 0 && (
                <span className="min-w-[18px] h-[18px] px-1 rounded-full bg-[var(--primary)] text-white text-[10px] font-bold flex items-center justify-center">
                  {savedCount}
                </span>
              )}
            </button>
          ))}
        </nav>

        {/* Profile action */}
        <button
          onClick={onOpenProfile}
          className="btn btn-secondary text-xs px-3 py-1.5"
        >
          <span
            className={`w-2 h-2 rounded-full ${hasProfile ? "bg-emerald-500" : "bg-amber-500"}`}
          />
          <span className="hidden sm:inline">{hasProfile ? "My Profile" : "Set Profile"}</span>
        </button>
      </header>

      {/* Mobile bottom tab bar */}
      <nav className="md:hidden fixed bottom-0 inset-x-0 z-40 bg-white border-t border-[var(--border-color)] flex items-stretch shadow-[0_-2px_12px_rgba(15,23,42,0.06)]">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 flex flex-col items-center justify-center gap-0.5 py-2 text-[11px] font-medium relative ${
              activeTab === tab.id ? "text-[var(--primary)]" : "text-[var(--text-dim)]"
            }`}
          >
            <span className="text-base leading-none">{tab.icon}</span>
            <span>{tab.label === "Recommendations" ? "For You" : tab.label}</span>
            {tab.id === "saved" && savedCount > 0 && (
              <span className="absolute top-1 right-1/2 translate-x-3 min-w-[16px] h-[16px] px-1 rounded-full bg-[var(--primary)] text-white text-[9px] font-bold flex items-center justify-center">
                {savedCount}
              </span>
            )}
          </button>
        ))}
      </nav>
    </>
  );
};
