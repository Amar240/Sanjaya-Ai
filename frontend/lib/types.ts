export type ProgramLevel = "UG" | "GR";
export type PlanMode = "CORE" | "FUSION";
export type Term = "Fall" | "Spring" | "Summer" | "Winter";

export type RoleOption = {
  role_id: string;
  title: string;
  market_grounding?: "direct" | "composite";
  fusion_available?: boolean;
};

export type StudentProfileInput = {
  level: ProgramLevel;
  mode: PlanMode;
  fusion_domain?: string | null;
  current_semester: number;
  start_term: Term;
  include_optional_terms: boolean;
  completed_courses: string[];
  min_credits: number;
  target_credits: number;
  max_credits: number;
  interests: string[];
};

export type PlanRequest = {
  student_profile: StudentProfileInput;
  preferred_role_id?: string | null;
  requested_role_text?: string | null;
};

export type SkillCoverage = {
  required_skill_id: string;
  covered: boolean;
  matched_courses: string[];
};

export type PlanSemester = {
  semester_index: number;
  term: Term;
  courses: string[];
  total_credits: number;
  warnings: string[];
};

export type EvidencePanelItem = {
  evidence_id: string;
  role_id: string;
  skill_id: string;
  skill_name: string;
  source_id: string;
  source_provider: string;
  source_title: string;
  source_url: string;
  snippet: string;
  retrieval_method: "vector" | "lexical" | "hybrid";
  rank_score?: number | null;
  confidence?: number | null;
};

export type CoursePurposeCard = {
  course_id: string;
  course_title: string;
  why_this_course: string;
  satisfied_skills: string[];
  evidence: EvidencePanelItem[];
};

export type FusionReadiness = {
  domain_ready_pct: number;
  tech_ready_pct: number;
  overall_fit_pct: number;
};

export type FusionUnlockSkillStatus = {
  skill_id: string;
  reason: string;
  covered: boolean;
  matched_courses: string[];
};

export type FusionSummary = {
  domain: string;
  domain_weight: number;
  tech_weight: number;
  domain_skill_coverage: SkillCoverage[];
  tech_skill_coverage: SkillCoverage[];
  unlock_skills: FusionUnlockSkillStatus[];
  readiness: FusionReadiness;
};

export type CandidateRole = {
  role_id: string;
  role_title: string;
  score: number;
  reasons: string[];
};

export type PlanError = {
  code:
    | "COURSE_NOT_FOUND"
    | "PREREQ_ORDER"
    | "CREDIT_OVER_MAX"
    | "CREDITS_BELOW_MIN"
    | "LEVEL_MISMATCH"
    | "OFFERING_MISMATCH"
    | "DUPLICATE_COURSE"
    | "ANTIREQ_CONFLICT"
    | "COREQ_NOT_SATISFIED"
    | "SKILL_GAP"
    | "PREREQ_EXTERNAL_REF"
    | "PREREQ_COMPLEX_UNSUPPORTED"
    | "EVIDENCE_INTEGRITY_VIOLATION"
    | "ROLE_REQUEST_UNRESOLVED";
  message: string;
  course_id?: string | null;
  prereq_id?: string | null;
  term?: Term | null;
  details?: Record<string, unknown>;
};

export type RoleRequestItem = {
  role_request_id: string;
  role_query_norm: string;
  examples: string[];
  count: number;
  first_seen: string;
  last_seen: string;
  top_candidates: { role_id: string; score: number }[];
  status: "open" | "mapped" | "created_role" | "ignored";
  resolution: {
    mapped_role_id?: string | null;
    new_role_id?: string | null;
    note?: string | null;
  };
};

export type InsightsSummary = {
  window: string;
  events_total: number;
  top_roles_selected: { key: string; count: number }[];
  top_role_searches: { key: string; count: number }[];
  top_unknown_role_requests: {
    role_request_id: string;
    role_query_norm: string;
    count: number;
    status: string;
  }[];
  top_error_codes: { key: string; count: number }[];
  top_intents: { key: string; count: number }[];
  severity_breakdown: { warnings: number; errors: number };
};

export type NodeTiming = {
  node: string;
  timing_ms: number;
};

export type PlanResponse = {
  request_id: string;
  plan_id: string;
  cache_status: "hit" | "miss";
  data_version: string;
  selected_role_id: string;
  selected_role_title: string;
  skill_coverage: SkillCoverage[];
  semesters: PlanSemester[];
  validation_errors: PlanError[];
  notes: string[];
  candidate_roles: CandidateRole[];
  evidence_panel?: EvidencePanelItem[];
  course_purpose_cards?: CoursePurposeCard[];
  fusion_summary?: FusionSummary | null;
  agent_trace?: string[];
  node_timings?: NodeTiming[];
};

export type ChatTurn = {
  role: "user" | "assistant";
  content: string;
  timestamp_utc: string;
};

export type ChatRoleSuggestion = {
  role_id: string;
  title: string;
};

export type ChatProfileDraft = {
  level: ProgramLevel;
  mode: PlanMode;
  fusion_domain?: string | null;
  current_semester: number;
  start_term: Term;
  include_optional_terms: boolean;
  completed_courses: string[];
  min_credits: number;
  target_credits: number;
  max_credits: number;
  interests: string[];
  preferred_role_id?: string | null;
};

export type ChatRequest = {
  message: string;
  session_id?: string | null;
  reset_session?: boolean;
};

export type ChatResponse = {
  session_id: string;
  assistant_message: string;
  profile_draft: ChatProfileDraft;
  missing_fields: string[];
  suggested_roles: ChatRoleSuggestion[];
  ready_for_plan: boolean;
  plan_request_draft?: PlanRequest | null;
  conversation: ChatTurn[];
  llm_used: boolean;
};

export type AdvisorRequest = {
  question: string;
  plan_id?: string;
  plan?: PlanResponse;
  tone?: "friendly" | "concise";
};

export type AdvisorCitation = {
  citation_type:
    | "evidence_source"
    | "course"
    | "policy_note"
    | "skill_coverage"
    | "semester";
  label: string;
  detail: string;
  source_url?: string | null;
  evidence_id?: string | null;
  course_id?: string | null;
  skill_id?: string | null;
};

export type AdvisorResponse = {
  request_id: string;
  plan_id: string;
  intent: string;
  answer: string;
  reasoning_points: string[];
  citations: AdvisorCitation[];
  confidence: number;
  used_llm: boolean;
  llm_status: "used" | "fallback" | "disabled";
  llm_error?: string | null;
};
