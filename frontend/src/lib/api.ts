const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";

function getToken(): string | null {
  return localStorage.getItem("mlens_token");
}

export function setToken(token: string) {
  localStorage.setItem("mlens_token", token);
}

export function clearToken() {
  localStorage.removeItem("mlens_token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore parse error */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  // Auth
  register: (email: string, password: string, full_name: string) =>
    request<import("../types").User>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    }),
  login: (email: string, password: string) =>
    request<{ access_token: string; token_type: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  // Research
  createResearch: (payload: {
    query: string;
    geography?: string;
    time_period?: string;
    depth?: string;
    competitors?: string[];
  }) =>
    request<import("../types").ResearchJob>("/research", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listResearch: () => request<import("../types").ResearchProject[]>("/research"),
  getResearchProject: (projectId: string) =>
    request<import("../types").ResearchProjectDetail>(`/research/${projectId}`),
  runResearch: (jobId: string) =>
    request<import("../types").ResearchJob>(`/research/${jobId}/run`, { method: "POST" }),
  getStatus: (jobId: string) => request<import("../types").ResearchStatus>(`/research/${jobId}/status`),
  getSources: (jobId: string) => request<import("../types").SourceItem[]>(`/research/${jobId}/sources`),
  getCompetitors: (jobId: string) =>
    request<import("../types").CompetitorItem[]>(`/research/${jobId}/competitors`),
  getTrends: (jobId: string) => request<import("../types").TrendItem[]>(`/research/${jobId}/trends`),
  getSentiment: (jobId: string) =>
    request<import("../types").SentimentItem[]>(`/research/${jobId}/sentiment`),
  getRecommendations: (jobId: string) =>
    request<import("../types").RecommendationItem[]>(`/research/${jobId}/recommendations`),
  getReport: (jobId: string) => request<import("../types").ReportData>(`/research/${jobId}/report`),
  exportReport: async (jobId: string, fmt: "json" | "markdown" | "pdf") => {
    const token = getToken();
    const res = await fetch(`${API_BASE}/research/${jobId}/export?fmt=${fmt}`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error("Export failed");
    return res.blob();
  },
  whatChanged: (projectId: string) =>
    request<import("../types").WhatChanged>(`/research/${projectId}/what-changed`),
  compare: (companies: string[]) =>
    request<import("../types").ResearchJob>("/compare", {
      method: "POST",
      body: JSON.stringify({ companies }),
    }),
};
