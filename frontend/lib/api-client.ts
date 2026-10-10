import { reportClientError } from "@/lib/error-reporting";

const API_BASE_URL = process.env.NEXT_PUBLIC_BANKWISE_API_URL?.replace(/\/$/, "");

export class ApiError extends Error {
  status: number;
  requestId?: string;

  constructor(message: string, status: number, requestId?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.requestId = requestId;
  }
}

function publicErrorMessage(status: number): string {
  if (status === 401) return "Authentication is required. Please sign in and try again.";
  if (status === 403) return "This request could not be verified. Refresh and try again.";
  if (status === 404) return "The requested item could not be found.";
  if (status === 429) return "Too many requests. Please wait a moment and try again.";
  if (status >= 500) return "Bankwise is temporarily unavailable. Please try again shortly.";
  if (status === 400 || status === 422) return "Please check your request and try again.";
  return "The request could not be completed. Please try again.";
}

function apiUrl(path: string): string {
  return API_BASE_URL ? `${API_BASE_URL}${path}` : path;
}

async function getCsrfToken(): Promise<string> {
  let response: Response;
  try {
    response = await fetch(apiUrl("/api/auth/csrf"), { credentials: "include" });
  } catch {
    reportClientError("network");
    throw new Error("Could not establish a secure session. Please retry.");
  }
  if (!response.ok) {
    if (response.status >= 500) {
      reportClientError("api_server", response.headers.get("X-Request-ID") || undefined);
    }
    throw new Error("Could not establish a secure session. Please retry.");
  }
  const result = (await response.json()) as { csrfToken: string };
  return result.csrfToken;
}

export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const method = (init.method || "GET").toUpperCase();
  const headers = new Headers(init.headers);
  if (method !== "GET" && method !== "HEAD" && method !== "OPTIONS") {
    headers.set("X-CSRF-Token", await getCsrfToken());
  }
  let response: Response;
  try {
    response = await fetch(apiUrl(path), {
      ...init,
      headers,
      credentials: "include",
    });
  } catch {
    reportClientError("network");
    throw new Error("Could not reach BankWise API. Check that the backend is running.");
  }
  if (!response.ok) {
    if (response.status >= 500) {
      reportClientError("api_server", response.headers.get("X-Request-ID") || undefined);
    }
    if (
      response.status === 401 &&
      typeof window !== "undefined" &&
      path !== "/api/auth/me" &&
      path !== "/api/auth/session"
    ) {
      window.dispatchEvent(new Event("bankwise:unauthorized"));
    }
    throw new ApiError(
      publicErrorMessage(response.status),
      response.status,
      response.headers.get("X-Request-ID") || undefined,
    );
  }
  return response;
}
