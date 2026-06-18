import type { SessionData } from "./backend-types";

export function getApiBaseUrl() {
  return "/api";
}

type ApiOptions = RequestInit & {
  session?: SessionData | null;
};

export async function apiRequest<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const { session, headers, body, ...rest } = options;
  const requestHeaders = new Headers(headers);

  if (session?.access_token) {
    requestHeaders.set("Authorization", `Bearer ${session.access_token}`);
  }

  const isFormData = typeof FormData !== "undefined" && body instanceof FormData;
  if (body !== undefined && body !== null && !isFormData && !requestHeaders.has("Content-Type")) {
    requestHeaders.set("Content-Type", "application/json");
  }

  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...rest,
    headers: requestHeaders,
    body,
    cache: "no-store",
  });

  const text = await response.text();
  let data: unknown = null;

  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!response.ok) {
    const detail =
      typeof data === "object" && data !== null && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : typeof data === "string" && data.trim()
          ? data
          : `Request failed with status ${response.status}`;
    throw new Error(detail);
  }

  return data as T;
}
