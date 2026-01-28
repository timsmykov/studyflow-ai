// API client for StudyFlow backend

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface StreamChunk {
  session_id: number;
  message_id: number;
  content: string;
  delta: string;
  finished: boolean;
}

// Get auth token from localStorage (set by Clerk)
function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("__clerk_client_jwt");
}

// API headers with auth
function getHeaders(): HeadersInit {
  const token = getAuthToken();
  return {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
  };
}

// Fetch wrapper with error handling
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: { ...getHeaders(), ...options.headers },
  });

  if (!response.ok) {
    if (response.status === 401) {
      // Redirect to sign-in on auth error
      window.location.href = "/sign-in";
    }
    const error = await response.json();
    throw new Error(error.detail || "API request failed");
  }

  return response.json();
}

// Streaming chat (SSE)
export async function* chatStream(
  session_id: number | null,
  course_id: string,
  message: string,
  complexity: "brief" | "standard" | "deep" = "standard"
): AsyncGenerator<string, void, unknown> {
  const response = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ session_id, course_id, message, complexity }),
  });

  if (!response.ok) {
    throw new Error("Failed to start chat stream");
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("Response body not readable");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const data = line.slice(6);
      if (data === "[DONE]") break;

      try {
        const chunk: StreamChunk = JSON.parse(data);
        if (chunk.delta) yield chunk.delta;
      } catch (e) {
        console.error("Failed to parse SSE chunk:", e);
      }
    }
  }
}

// Non-streaming chat
export async function chat(
  session_id: number | null,
  course_id: string,
  message: string,
  complexity: "brief" | "standard" | "deep" = "standard"
) {
  return apiFetch<{ session_id: number; message: string; tokens: number }>("/chat", {
    method: "POST",
    body: JSON.stringify({ session_id, course_id, message, complexity }),
  });
}

// Students
export async function getCurrentStudent() {
  return apiFetch<{ id: number; clerk_id: string }>("/students/me");
}

export async function getStudents() {
  return apiFetch<any[]>("/students");
}

export async function createStudent(clerk_id: string) {
  return apiFetch<{ id: number }>("/students", {
    method: "POST",
    body: JSON.stringify({ clerk_id }),
  });
}

// Sessions
export async function createSession(course_id: string) {
  return apiFetch<{ id: number }>(`/students/me/sessions`, {
    method: "POST",
    body: JSON.stringify({ course_id }),
  });
}

export async function getStudentSessions(student_id: number) {
  return apiFetch<any[]>(`/students/${student_id}/sessions`);
}

// Messages
export async function getSessionMessages(session_id: number) {
  return apiFetch<any[]>(`/sessions/${session_id}/messages`);
}

// Progress (BKT)
export async function updateProgress(
  student_id: number,
  skill_id: string,
  correct: boolean
) {
  const endpoint = correct ? "correct" : "incorrect";
  return apiFetch<{ mastery: number }>(
    `/students/${student_id}/skills/${skill_id}/${endpoint}`,
    { method: "POST" }
  );
}

export async function getStudentSkills(student_id: number) {
  return apiFetch<any[]>(`/students/${student_id}/skills`);
}

// Dropout prediction
export async function getDropoutRisk(student_id: number) {
  return apiFetch<{ risk_score: number }>(`/students/${student_id}/dropout-risk`);
}

export async function getAllStudentsWithRisk() {
  return apiFetch<any[]>("/analytics/students");
}

// Health check
export async function healthCheck() {
  return apiFetch<{ status: string }>("/health");
}
