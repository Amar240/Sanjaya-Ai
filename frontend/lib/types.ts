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
  role_id: string;
  skill_id: string;
  skill_name: string;
  source_id: string;
  source_provider: string;
  source_title: string;
  source_url: string;
  snippet: string;
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

export type PlanResponse = {
  selected_role_id: string;
  selected_role_title: string;
  skill_coverage: SkillCoverage[];
  semesters: PlanSemester[];
  validation_errors: string[];
  notes: string[];
  evidence_panel?: EvidencePanelItem[];
  course_purpose_cards?: CoursePurposeCard[];
  fusion_summary?: FusionSummary | null;
  agent_trace?: string[];
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
  plan: PlanResponse;
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
};

export type AdvisorResponse = {
  intent: string;
  answer: string;
  reasoning_points: string[];
  citations: AdvisorCitation[];
  confidence: number;
  used_llm: boolean;
  llm_status: "used" | "fallback" | "disabled";
  llm_error?: string | null;
};
