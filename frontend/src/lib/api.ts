export interface ClarifyingQuestionOption {
  label: string;
  value: any;
}

export interface ClarifyingQuestion {
  field: string;
  prompt: string;
  options: ClarifyingQuestionOption[] | null;
}

export interface ParseQueryResult {
  locale: string;
  locale_message: string | null;
  intent: string;
  fields: Record<string, any>;
  display: Record<string, any>;
  needs: Array<{ need_code: string; confidence: number; explicit: boolean }>;
  life_events: Array<{ event_code: string; from_value: string | null; to_value: string | null }>;
  missing_blocking: string[];
  clarifying_questions: ClarifyingQuestion[];
  original_query: string;
  names_schemes: boolean;
}

export interface RuleTrace {
  rule_type: string;
  requirement: any;
  your_value: any;
  result: "pass" | "fail" | "unknown";
  required: boolean;
  message: string;
}

export interface SchemeSource {
  official_source: string | null;
  official_application_url: string | null;
}

export interface SchemeRule {
  rule_type: string;
  op: string;
  value: any;
  required: boolean;
}

export interface SchemeTrust {
  claim_level: "assertive" | "hedged" | "discovery_only";
  qualifier: string | null;
  source_line: string;
  confidence: number | null;
  as_of: string | null;
}

export interface SchemeItem {
  id: string;
  scheme_id: string;
  scheme_name: string;
  category: string;
  state: string | null;
  district: string | null;
  description: string;
  benefits_summary: string | null;
  application_status: string | null;
  verification_status: string;
  is_demo: boolean;
  demo_banner: string;
  deadline: string | null;
  sources: SchemeSource[];
  rules: SchemeRule[];
  eligibility_status: "eligible" | "likely_eligible" | "needs_more_information" | "not_eligible";
  score: number;
  components: Record<string, number>;
  semantic: number;
  traces: RuleTrace[];
  need_group: string;
  reasons: string[];
  why_not: Array<{ rule_type: string; requirement: any; your_value: any; message: string }> | null;
  expired: boolean;
  rank?: number;
  trust: SchemeTrust;
}

export interface OpportunityMapItem {
  category: string;
  count: number;
  bar: number;
}

export interface ExploreOtherItem {
  need_code: string;
  label: string;
  category: string;
}

export interface NoMatchExplanation {
  reason: "unclear_concern" | "no_data_for_need" | "not_eligible";
  message: string;
}

export interface RecommendResponse {
  recommendations: SchemeItem[];
  grouped: Record<string, SchemeItem[]>;
  near_misses: SchemeItem[];
  opportunity_map: OpportunityMapItem[];
  explore_other: ExploreOtherItem[];
  weights: Record<string, number>;
  rejected_count: number;
  no_match_explanation: NoMatchExplanation | null;
}

export interface SavedSchemeItem {
  scheme_id: string;
  personal_status: "saved" | "need_to_apply" | "applied_reminder" | "expired";
}

export interface SavedSchemesResponse {
  note: string;
  items: SavedSchemeItem[];
}

export async function parseQuery(query: string): Promise<ParseQueryResult> {
  const res = await fetch("/api/parse-query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) {
    throw new Error(`Parse failed: ${res.statusText}`);
  }
  return res.json();
}

export async function getRecommendations(payload: {
  profile?: Record<string, any> | null;
  needs?: any[] | null;
  query?: string | null;
}): Promise<RecommendResponse> {
  const res = await fetch("/api/recommend", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(`Recommendations request failed: ${res.statusText}`);
  }
  return res.json();
}

export async function updateProfile(fields: Record<string, any>, sourceQuery?: string): Promise<any> {
  const res = await fetch("/api/profile/update", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fields, source_query: sourceQuery }),
  });
  if (!res.ok) {
    throw new Error(`Profile update failed: ${res.statusText}`);
  }
  return res.json();
}

export async function saveScheme(schemeId: string, personalStatus: string = "saved"): Promise<any> {
  const res = await fetch("/api/saved-schemes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scheme_id: schemeId, personal_status: personalStatus }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Failed to save scheme: ${res.statusText}`);
  }
  return res.json();
}

export async function getSavedSchemes(): Promise<SavedSchemesResponse> {
  const res = await fetch("/api/saved-schemes");
  if (!res.ok) {
    throw new Error(`Failed to fetch saved schemes: ${res.statusText}`);
  }
  return res.json();
}

export async function reportScheme(schemeId: string, reason: string): Promise<{ ok: boolean; message: string }> {
  const res = await fetch("/api/scheme-reports", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scheme_id: schemeId, reason }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Failed to submit report: ${res.statusText}`);
  }
  return res.json();
}

export async function resetProfile(): Promise<any> {
  const res = await fetch("/api/profile/reset", { method: "POST" });
  if (!res.ok) {
    throw new Error(`Profile reset failed: ${res.statusText}`);
  }
  return res.json();
}
