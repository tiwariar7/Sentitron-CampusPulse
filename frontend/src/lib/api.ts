// Client side API fetch utility with automatic JWT token attachment
export async function apiFetch(url: string, options: RequestInit = {}): Promise<Response> {
  let token = null;
  if (typeof window !== "undefined") {
    token = localStorage.getItem("token");
  }

  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  } as Record<string, string>;

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Ensure absolute URL to backend
  const finalUrl = url.startsWith("http") ? url : `http://localhost:8000${url}`;

  const response = await fetch(finalUrl, {
    ...options,
    headers,
  });

  return response;
}
