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

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data?: any) {
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

    let data: any = null;
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      data = await response.json();
    }

    if (!response.ok) {
      let errorMessage = friendlyHttpMessage(response.status, response.statusText);

      if (data && typeof data === "object") {
        if (data.error && typeof data.error === "object") {
          if (typeof data.error.message === "string" && data.error.message.trim()) {
            errorMessage = data.error.message;
          }
        } else if (typeof data.detail === "string") {
          errorMessage = data.detail;
        } else if (Array.isArray(data.detail)) {
          errorMessage = data.detail
            .map((err: { loc?: string[]; msg?: string }) => `${err.loc?.join(".") || "field"}: ${err.msg}`)
            .join("; ");
        } else if (typeof data.message === "string") {
          errorMessage = data.message;
        }
      }

      throw new ApiError(errorMessage, response.status, data);
    }

    return data as T;
  } catch (err: any) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(
      err.message === "Failed to fetch"
        ? "Unable to connect to Apex Sales AI API. Please ensure the backend is running."
        : err.message || "An unexpected network error occurred.",
      0
    );
  }
}

export const apiClient = {
  get<T>(endpoint: string): Promise<T> {
    return request<T>(endpoint, { method: "GET" });
  },

  post<T>(endpoint: string, body?: any): Promise<T> {
    return request<T>(endpoint, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    });
  },

  patch<T>(endpoint: string, body?: any): Promise<T> {
    return request<T>(endpoint, {
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    });
  },
};
