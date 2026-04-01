const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers);
  
  // Set default JSON content type unless body is FormData (e.g. for uploads)
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  // Attach JWT token from localStorage if available
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("truthlens_access_token");
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = `API error: ${response.status}`;
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorDetail = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
      }
    } catch {
      // Ignored if response is not JSON
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

// Convenience methods
export const api = {
  get: (endpoint: string) => fetchApi(endpoint, { method: "GET" }),
  post: (endpoint: string, body: any) => 
    fetchApi(endpoint, { method: "POST", body: body instanceof FormData ? body : JSON.stringify(body) }),
  put: (endpoint: string, body: any) => 
    fetchApi(endpoint, { method: "PUT", body: body instanceof FormData ? body : JSON.stringify(body) }),
  delete: (endpoint: string) => fetchApi(endpoint, { method: "DELETE" }),
};
