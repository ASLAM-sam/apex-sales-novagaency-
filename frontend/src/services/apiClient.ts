import { API_BASE_URL } from "../config";

export class ApiError extends Error {
  status: number;
  data: any;

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
      let errorMessage = `HTTP Error ${response.status}: ${response.statusText}`;

      if (data && typeof data === "object") {
        if (typeof data.detail === "string") {
          errorMessage = data.detail;
        } else if (Array.isArray(data.detail)) {
          // FastAPI 422 validation error
          errorMessage = data.detail.map((err: any) => `${err.loc?.join(".") || "field"}: ${err.msg}`).join("; ");
        } else if (data.message) {
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
