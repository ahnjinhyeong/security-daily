"use client";

import { FormEvent, useState, useTransition } from "react";
import { gradeQuizAnswer, type QuizActionState } from "@/app/actions";
import type { Quiz } from "@/lib/types";
import styles from "./dashboard.module.css";

export function QuizCard({ quiz, index }: { quiz: Quiz; index: number }) {
  const [answer, setAnswer] = useState("");
  const [state, setState] = useState<QuizActionState>({ status: "idle" });
  const [isPending, startTransition] = useTransition();
  const completed = state.status === "success";

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (completed || isPending) return;
    startTransition(async () => setState(await gradeQuizAnswer(quiz.id, answer)));
  }

  return (
    <article className={styles.quizCard}>
      <span className={styles.quizNumber}>QUIZ {String(index + 1).padStart(2, "0")}</span>
      <h3>{quiz.question}</h3>
      <form onSubmit={submit} className={styles.quizForm}>
        <label htmlFor={`answer-${quiz.id}`}>단답형 답안</label>
        <div className={styles.answerRow}>
          <input
            id={`answer-${quiz.id}`}
            value={answer}
            onChange={(event) => setAnswer(event.target.value)}
            placeholder="답안을 입력하세요"
            autoComplete="off"
            disabled={completed || isPending}
            required
          />
          <button type="submit" disabled={completed || isPending || !answer.trim()}>
            {isPending ? "채점 중…" : completed ? "제출 완료" : "답안 제출"}
          </button>
        </div>
      </form>
      <div aria-live="polite">
        {state.status === "error" && <p className={styles.formError}>{state.message}</p>}
        {state.status === "success" && (
          <div className={`${styles.quizResult} ${state.result.correct ? styles.correct : styles.incorrect}`}>
            <strong>{state.result.correct ? "정답입니다" : "다시 기억해 두세요"}</strong>
            <dl><div><dt>정답</dt><dd>{state.result.correct_answer}</dd></div></dl>
            <p>{state.result.explanation}</p>
          </div>
        )}
      </div>
    </article>
  );
}
