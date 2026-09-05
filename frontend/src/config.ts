const configured = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();
export const API_BASE_URL = configured && configured.length > 0 ? configured.replace(/\/$/, "") : "";
