"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/Header";
import { SearchBox } from "@/components/SearchBox";
import { ProfileWizard } from "@/components/ProfileWizard";
import { SchemeCard } from "@/components/SchemeCard";
import { ExplainabilityDrawer } from "@/components/ExplainabilityDrawer";
import { OpportunityMap } from "@/components/OpportunityMap";
import { SavedSchemesView } from "@/components/SavedSchemesView";
import {
  parseQuery,
  getRecommendations,
  updateProfile,
  saveScheme,
  getSavedSchemes,
  SchemeItem,
  RecommendResponse,
  ParseQueryResult,
  SavedSchemeItem,
} from "@/lib/api";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"results" | "grouped" | "opportunity" | "saved">("results");
  const [queryText, setQueryText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Profile state
  const [profile, setProfile] = useState<Record<string, any>>({});
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  // API Responses
  const [parseResult, setParseResult] = useState<ParseQueryResult | null>(null);
  const [recommendData, setRecommendData] = useState<RecommendResponse | null>(null);
  const [savedSchemes, setSavedSchemes] = useState<SavedSchemeItem[]>([]);
  const [savedNote, setSavedNote] = useState<string>("");

  // Category filter
  const [selectedCategory, setSelectedCategory] = useState<string>("All");

  // Selected scheme for explainability drawer
  const [explainScheme, setExplainScheme] = useState<SchemeItem | null>(null);

  // Initial load: Fetch default recommendations & saved schemes
  const fetchInitialData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const recs = await getRecommendations({});
      setRecommendData(recs);
      const saved = await getSavedSchemes().catch(() => ({ note: "", items: [] }));
      setSavedSchemes(saved.items || []);
      setSavedNote(saved.note || "");
    } catch (err: any) {
      setError(err.message || "Failed to connect to CivicGuide backend services.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchInitialData();
  }, [fetchInitialData]);

  // Handle Search Submission
  const handleSearch = async (userQuery: string) => {
    setQueryText(userQuery);
    setLoading(true);
    setError(null);
    try {
      // Step 1: Parse NLP query
      const parsed = await parseQuery(userQuery);
      setParseResult(parsed);

      // Merge extracted fields into current profile
      const newFields = { ...profile, ...parsed.fields };
      setProfile(newFields);

      // Step 2: Get recommendations
      const recs = await getRecommendations({
        profile: newFields,
        needs: parsed.needs,
        query: userQuery,
      });
      setRecommendData(recs);
    } catch (err: any) {
      setError(err.message || "Could not complete natural language query search.");
    } finally {
      setLoading(false);
    }
  };

  // Handle Profile Update from Wizard
  const handleSaveProfile = async (fields: Record<string, any>) => {
    setLoading(true);
    setError(null);
    try {
      await updateProfile(fields, queryText || undefined);
      setProfile(fields);
      const recs = await getRecommendations({
        profile: fields,
        query: queryText || undefined,
      });
      setRecommendData(recs);
    } catch (err: any) {
      setError(err.message || "Failed to update profile.");
    } finally {
      setLoading(false);
    }
  };

  // Handle Scheme Save / Bookmark
  const handleSaveScheme = async (schemeId: string, status: string) => {
    try {
      await saveScheme(schemeId, status);
      const refreshed = await getSavedSchemes();
      setSavedSchemes(refreshed.items || []);
    } catch (err: any) {
      alert(err.message || "Save scheme failed.");
    }
  };

  // Saved map lookup
  const savedMap = new Map(savedSchemes.map((s) => [s.scheme_id, s.personal_status]));

  // Filter recommendations by selected category
  const filteredRecommendations = (recommendData?.recommendations || []).filter((sc) => {
    if (selectedCategory === "All") return true;
    return sc.category === selectedCategory;
  });

  const categories = [
    "All",
    ...Array.from(new Set((recommendData?.recommendations || []).map((s) => s.category))),
  ];

  return (
    <div className="min-h-screen flex flex-col bg-[var(--bg-main)] text-[var(--text-main)]">
      {/* Navigation Bar */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        savedCount={savedSchemes.length}
        onOpenProfile={() => setIsProfileOpen(true)}
        hasProfile={Object.keys(profile).some((k) => profile[k] !== null && profile[k] !== "")}
      />

      {/* Main Container */}
      <main className="flex-1 w-full max-w-6xl mx-auto px-4 lg:px-8 py-8 pb-24 md:pb-8 space-y-8">
        {/* Landing Hero Section */}
        <section className="text-center space-y-3 pt-2">
          <div className="chip inline-flex bg-[var(--primary-soft-bg)] border-[var(--primary-soft-border)] text-[var(--primary-soft-text)] font-bold uppercase tracking-wide">
            🏛️ Civic Intelligence Engine
          </div>
          <h1 className="text-3xl md:text-5xl font-extrabold text-[var(--text-main)] tracking-tight leading-tight">
            Discover Government Schemes You're <span className="text-[var(--primary)]">Eligible</span> For
          </h1>
          <p className="text-sm md:text-base text-[var(--text-muted)] max-w-2xl mx-auto leading-relaxed">
            Describe what you need in plain language. CivicGuide evaluates factual eligibility rules and ranks government benefits transparently — no guesswork.
          </p>
        </section>

        {/* Natural Language Search Component */}
        <section>
          <SearchBox onSearch={handleSearch} loading={loading} />
        </section>

        {/* Error Notification Banner */}
        {error && (
          <div className="bg-[var(--status-not-bg)] border border-[var(--status-not-border)] rounded-xl p-4 text-xs font-semibold text-[var(--status-not-text)] flex items-center justify-between">
            <span>⚠️ {error}</span>
            <button onClick={() => setError(null)} className="font-bold hover:opacity-70">
              Dismiss
            </button>
          </div>
        )}

        {/* Multilingual / Locale Notification */}
        {parseResult?.locale_message && (
          <div className="bg-[var(--status-likely-bg)] border border-[var(--status-likely-border)] rounded-xl p-3.5 text-xs text-[var(--status-likely-text)] font-medium">
            ℹ️ {parseResult.locale_message}
          </div>
        )}

        {/* Clarifying Questions Prompt Banner */}
        {parseResult?.clarifying_questions && parseResult.clarifying_questions.length > 0 && (
          <div className="card p-4 border-[var(--primary-soft-border)] flex items-center justify-between flex-wrap gap-3">
            <div>
              <span className="text-xs font-bold text-[var(--primary)] uppercase tracking-wide">
                Clarification needed for exact eligibility
              </span>
              <p className="text-xs text-[var(--text-muted)] mt-0.5">
                Some key details (like state residency or annual income) weren't mentioned. Update your profile for exact results.
              </p>
            </div>
            <button onClick={() => setIsProfileOpen(true)} className="btn btn-primary text-xs px-4 py-1.5">
              Answer questions
            </button>
          </div>
        )}

        {/* Main Content Views */}
        {activeTab === "results" && (
          <div className="space-y-6">
            {/* Category Filter Chips */}
            {categories.length > 1 && (
              <div className="flex items-center gap-2 overflow-x-auto pb-1 -mx-1 px-1">
                <span className="text-xs font-semibold text-[var(--text-dim)] mr-1 shrink-0">Category:</span>
                {categories.map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setSelectedCategory(cat)}
                    className={`px-3 py-1 rounded-lg text-xs font-medium border transition-colors whitespace-nowrap shrink-0 ${
                      selectedCategory === cat
                        ? "bg-[var(--primary)] text-white border-[var(--primary)]"
                        : "bg-white text-[var(--text-muted)] border-[var(--border-color)] hover:border-[var(--primary-soft-border)]"
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            )}

            {/* Scheme Cards Grid */}
            {filteredRecommendations.length === 0 ? (
              <div className="card p-12 text-center space-y-3">
                <span className="text-4xl block">
                  {recommendData?.no_match_explanation?.reason === "not_eligible" ? "🚫" : recommendData?.no_match_explanation?.reason === "no_data_for_need" ? "📭" : "🔍"}
                </span>
                <h3 className="text-base font-bold text-[var(--text-main)]">
                  {recommendData?.no_match_explanation?.reason === "not_eligible"
                    ? "No Eligible Schemes Found"
                    : recommendData?.no_match_explanation?.reason === "no_data_for_need"
                    ? "Nothing In Our Database Yet"
                    : "No Schemes Found"}
                </h3>
                <p className="text-xs text-[var(--text-muted)] max-w-sm mx-auto">
                  {recommendData?.no_match_explanation?.message ||
                    "Try adjusting your query or updating your profile details in the profile wizard."}
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredRecommendations.map((scheme, idx) => (
                  <SchemeCard
                    key={scheme.scheme_id}
                    scheme={scheme}
                    rank={idx + 1}
                    onOpenExplain={(sc) => setExplainScheme(sc)}
                    onSaveScheme={handleSaveScheme}
                    savedStatus={savedMap.get(scheme.scheme_id)}
                  />
                ))}
              </div>
            )}

            {/* Near Misses Section */}
            {recommendData?.near_misses && recommendData.near_misses.length > 0 && (
              <div className="pt-6 space-y-4">
                <div className="border-t border-[var(--border-color)] pt-6">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-[var(--status-likely-text)]">⚡ Near-Miss Schemes</span>
                    <span className="text-xs text-[var(--text-dim)]">
                      (Ineligible by 1 rule, but satisfied 2+ criteria)
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {recommendData.near_misses.map((scheme) => (
                    <SchemeCard
                      key={scheme.scheme_id}
                      scheme={scheme}
                      onOpenExplain={(sc) => setExplainScheme(sc)}
                      onSaveScheme={handleSaveScheme}
                      savedStatus={savedMap.get(scheme.scheme_id)}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Grouped by Need Tab */}
        {activeTab === "grouped" && recommendData?.grouped && (
          <div className="space-y-8">
            {Object.entries(recommendData.grouped).map(([grpName, schemes]) => (
              <div key={grpName} className="space-y-4">
                <div className="flex items-center gap-3 border-b border-[var(--border-color)] pb-2">
                  <h3 className="text-lg font-bold text-[var(--text-main)]">{grpName}</h3>
                  <span className="chip">{schemes.length} schemes</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {schemes.map((scheme, idx) => (
                    <SchemeCard
                      key={scheme.scheme_id}
                      scheme={scheme}
                      rank={idx + 1}
                      onOpenExplain={(sc) => setExplainScheme(sc)}
                      onSaveScheme={handleSaveScheme}
                      savedStatus={savedMap.get(scheme.scheme_id)}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Opportunity Map Tab */}
        {activeTab === "opportunity" && recommendData && (
          <OpportunityMap
            opportunityMap={recommendData.opportunity_map}
            exploreOther={recommendData.explore_other}
            onSelectCategory={(cat) => {
              setSelectedCategory(cat);
              setActiveTab("results");
            }}
          />
        )}

        {/* Saved Schemes Tab */}
        {activeTab === "saved" && (
          <SavedSchemesView
            savedItems={savedSchemes}
            allSchemes={recommendData?.recommendations || []}
            onOpenExplain={(sc) => setExplainScheme(sc)}
            onSaveScheme={handleSaveScheme}
            note={savedNote}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="mt-12 mb-16 md:mb-0 border-t border-[var(--border-color)] py-6 px-4 text-center text-xs text-[var(--text-dim)] space-y-1">
        <p className="font-semibold text-[var(--text-muted)]">
          CivicGuide — Natural Language Citizen Scheme Discovery Engine
        </p>
        <p>
          CivicGuide is an independent information tool. Official applications are submitted on official government portals.
        </p>
      </footer>

      {/* Profile Wizard Modal */}
      <ProfileWizard
        isOpen={isProfileOpen}
        onClose={() => setIsProfileOpen(false)}
        initialFields={profile}
        clarifyingQuestions={parseResult?.clarifying_questions}
        onSaveProfile={handleSaveProfile}
      />

      {/* Explainability Drawer Modal */}
      <ExplainabilityDrawer
        scheme={explainScheme}
        onClose={() => setExplainScheme(null)}
      />
    </div>
  );
}
