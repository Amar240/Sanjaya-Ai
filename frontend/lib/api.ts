import type {
  AdvisorRequest,
  AdvisorResponse,
  ChatRequest,
  ChatResponse,
  PlanRequest,
  PlanResponse,
  RoleOption
} from "@/lib/types";

async function parseJsonOrError(response: Response): Promise<unknown> {
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const detail =
      payload && typeof payload === "object" && "detail" in payload
        ? String((payload as { detail: unknown }).detail)
        : `Request failed with status ${response.status}`;
    throw new Error(detail);
  }
  return payload;
}

export async function fetchRoles(): Promise<RoleOption[]> {
  const response = await fetch("/api/roles", {
    method: "GET",
    cache: "no-store"
  });
  const payload = await parseJsonOrError(response);
  return payload as RoleOption[];
}

export async function createPlan(input: PlanRequest): Promise<PlanResponse> {
  const response = await fetch("/api/plan", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(input)
  });
  const payload = await parseJsonOrError(response);
  return payload as PlanResponse;
}

export async function sendChat(input: ChatRequest): Promise<ChatResponse> {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(input)
  });
  const payload = await parseJsonOrError(response);
  return payload as ChatResponse;
}

export async function askAdvisor(
  input: AdvisorRequest
): Promise<AdvisorResponse> {
  const response = await fetch("/api/advisor", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(input)
  });
  const payload = await parseJsonOrError(response);
  return payload as AdvisorResponse;
}
