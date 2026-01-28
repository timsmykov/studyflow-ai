// TypeScript types for StudyFlow API

export interface Student {
  id: number;
  clerk_id: string;
  created_at: string;
  last_active?: string;
}

export interface Session {
  id: number;
  student_id: number;
  course_id: string;
  created_at: string;
}

export interface MessageRole {
  USER: "user";
  ASSISTANT: "assistant";
  SYSTEM: "system";
}

export interface Message {
  id: number;
  session_id: number;
  role: "user" | "assistant" | "system";
  content: string;
  tokens: number;
  latency_ms: number;
  created_at: string;
}

export interface BKTProgress {
  id: number;
  student_id: number;
  skill_id: string;
  mastery: number;
  num_correct: number;
  num_incorrect: number;
  created_at: string;
  updated_at: string;
}

export interface DropoutPrediction {
  id: number;
  student_id: number;
  risk_score: number;
  features: Record<string, unknown>;
  predicted_at: string;
}

export interface ChatRequest {
  session_id?: number | null;
  course_id?: string;
  message: string;
  stream?: boolean;
}

export interface ChatResponse {
  session_id: number;
  message_id: number;
  content: string;
  tokens: number;
  latency_ms: number;
}

export interface ProgressUpdateRequest {
  correct: boolean;
}

export interface StudentWithRisk extends Student {
  dropout_risk?: number;
}

export type ComplexityLevel = "brief" | "standard" | "deep";
