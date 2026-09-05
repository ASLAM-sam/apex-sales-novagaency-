import { API_BASE_URL } from "../config";

function friendlyHttpMessage(status: number, statusText: string): string {
  switch (status) {
    case 400:
    case 422:
      return "The request could not be processed. Check the submitted values.";
    case 404:
      return "The requested record was not found.";
    case 409:
      return "This record already exists or conflicts with existing data.";
    case 429:
      return "Too many requests. Please wait and try again.";
    case 500:
    case 502:
    case 503:
    case 504:
      return "The server is unavailable. Please try again shortly.";
    default:
      return `Request failed (${status}${statusText ? `: ${statusText}` : ""}).`;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function extractErrorMessage(status: number, statusText: string, data: unknown): string {
  const fallback = friendlyHttpMessage(status, statusText);
  if (!isRecord(data)) return fallback;

  const error = data.error;
  if (isRecord(error) && typeof error.message === "string" && error.message.trim()) {
    return error.message;
  }
  if (typeof data.detail === "string" && data.detail.trim()) {
    return data.detail;
  }
  if (Array.isArray(data.detail)) {
    const details = data.detail
      .map((item) => {
        if (!isRecord(item)) return null;
        const loc = Array.isArray(item.loc) ? item.loc.join(".") : "field";
        const msg = typeof item.msg === "string" ? item.msg : null;
        return msg ? `${loc}: ${msg}` : null;
      })
      .filter((item): item is string => Boolean(item));
    if (details.length) return details.join("; ");
  }
  if (typeof data.message === "string" && data.message.trim()) {
    return data.message;
  }
  return fallback;
}

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    Accept: "application/json",
    ...options.headers,
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    let data: unknown = null;
    const contentType = response.headers.get("content-type") ?? "";
    if (contentType.includes("application/json")) {
      const text = await response.text();
      data = text ? JSON.parse(text) : null;
    }

    if (!response.ok) {
      throw new ApiError(extractErrorMessage(response.status, response.statusText, data), response.status, data);
    }

    return data as T;
  } catch (err: unknown) {
    if (err instanceof ApiError) {
      throw err;
    }
    const message = err instanceof Error ? err.message : "";
    throw new ApiError(
      message === "Failed to fetch" || message === "NetworkError when attempting to fetch resource."
        ? "Unable to connect to Apex Sales AI API. Please ensure the backend is running."
        : message || "An unexpected network error occurred.",
      0,
    );
  }
}

export const apiClient = {
  get<T>(endpoint: string): Promise<T> {
    return request<T>(endpoint, { method: "GET" });
  },

  post<T>(endpoint: string, body?: unknown): Promise<T> {
    return request<T>(endpoint, {
      method: "POST",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  },

  patch<T>(endpoint: string, body?: unknown): Promise<T> {
    return request<T>(endpoint, {
      method: "PATCH",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  },
};
