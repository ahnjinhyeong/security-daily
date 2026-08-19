import type { NewsBriefing, NewsDate, Quiz, QuizAnswerResult } from "./types";

const API_BASE_URL = process.env.BACKEND_API_BASE_URL;

export class ApiError extends Error {
  constructor(public readonly status: number, message = "API request failed") {
    super(message);
  }
}

function getApiBaseUrl(): string {
  if (!API_BASE_URL) {
    throw new Error("BACKEND_API_BASE_URL is not configured");
  }
  return API_BASE_URL.replace(/\/$/, "");
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...init,
    cache: "no-store",
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) throw new ApiError(response.status);
  return (await response.json()) as T;
}

export function getTodayNews(): Promise<NewsBriefing> {
  return request("/api/news/today");
}

export function getNewsByDate(date: string): Promise<NewsBriefing> {
  return request(`/api/news?date=${encodeURIComponent(date)}`);
}

export function getNewsDates(): Promise<NewsDate[]> {
  return request("/api/news/dates");
}

export function getTodayQuizzes(): Promise<Quiz[]> {
  return request("/api/quizzes/today");
}

export function getQuizzesByDate(date: string): Promise<Quiz[]> {
  return request(`/api/quizzes?date=${encodeURIComponent(date)}`);
}

export function submitQuizAnswer(quizId: number, answer: string): Promise<QuizAnswerResult> {
  return request(`/api/quizzes/${quizId}/answer`, {
    method: "POST",
    body: JSON.stringify({ answer }),
  });
}
