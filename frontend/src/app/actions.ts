"use server";

import { submitQuizAnswer } from "@/lib/api";
import type { QuizAnswerResult } from "@/lib/types";

export type QuizActionState =
  | { status: "idle" }
  | { status: "success"; result: QuizAnswerResult }
  | { status: "error"; message: string };

export async function gradeQuizAnswer(
  quizId: number,
  answer: string,
): Promise<QuizActionState> {
  if (!Number.isInteger(quizId) || quizId <= 0 || !answer.trim()) {
    return { status: "error", message: "답안을 입력해 주세요." };
  }
  try {
    return { status: "success", result: await submitQuizAnswer(quizId, answer) };
  } catch {
    return {
      status: "error",
      message: "답안을 채점하지 못했습니다. 잠시 후 다시 시도해 주세요.",
    };
  }
}
