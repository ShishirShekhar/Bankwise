const API_BASE_URL = process.env.NEXT_PUBLIC_BANKWISE_API_URL?.replace(/\/$/, "");

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function apiUrl(path: string): string {
  return API_BASE_URL ? `${API_BASE_URL}${path}` : path;
}

async function getCsrfToken(): Promise<string> {
  const response = await fetch(apiUrl("/api/auth/csrf"), { credentials: "include" });
  if (!response.ok) throw new Error("Could not establish a secure session. Please retry.");
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
    throw new Error("Could not reach BankWise API. Check that the backend is running.");
  }
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as
      | { detail?: string; message?: string }
      | null;
    if (
      response.status === 401 &&
      typeof window !== "undefined" &&
      path !== "/api/auth/me" &&
      path !== "/api/auth/session"
    ) {
      window.dispatchEvent(new Event("bankwise:unauthorized"));
    }
    throw new ApiError(
      payload?.detail || payload?.message || `Request failed (${response.status}).`,
      response.status,
    );
  }
  return response;
}
