"use client";

import { FormEvent, useState } from "react";
import { BookOpen, CheckCircle2, CircleAlert, LoaderCircle, MessageSquareText, Send } from "lucide-react";

import type { AdvisorAskResponse, AdvisorMissingData } from "@/types/finscope";

type AdvisorPanelProps = {
  answer: AdvisorAskResponse | null;
  disabled?: boolean;
  errorMessage: string;
  onAsk: (question: string) => void;
  onResolveMissing: (item: AdvisorMissingData) => void;
  status: "idle" | "loading" | "success" | "error";
};

const suggestedQuestions = [
  "Why is my budget under pressure?",
  "What should I fix first?",
  "How is inflation affecting me?",
  "What data is missing?",
  "How reliable is my forecast?"
];

function confidenceTone(confidence: string) {
  if (confidence === "high") return "text-teal";
  if (confidence === "medium") return "text-amber";
  return "text-rose";
}

function citationLabels(citations: AdvisorAskResponse["citations"]) {
  // Show the plain-English source name, never the internal document filename.
  return Array.from(new Set(citations.map((citation) => citation.source_label).filter(Boolean)));
}

function missingButtonLabel(item: AdvisorMissingData) {
  if (item.key.startsWith("category_")) return "Add row";
  if (item.key === "profile" || item.key === "monthly_income") return "Open profile";
  if (item.key === "transactions") return "Add transactions";
  return "Review";
}

export function AdvisorPanel({
  answer,
  disabled = false,
  errorMessage,
  onAsk,
  onResolveMissing,
  status
}: AdvisorPanelProps) {
  const [draftQuestion, setDraftQuestion] = useState(suggestedQuestions[0]);

  function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const question = draftQuestion.trim();
    if (!question || disabled || status === "loading") return;
    onAsk(question);
  }

  return (
    <div className="mx-auto grid max-w-7xl gap-5 px-5 py-6 lg:grid-cols-[0.85fr_1.15fr]">
      <section className="rounded-md border border-slate-200 bg-panel p-5 shadow-soft">
        <div className="mb-5 flex items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold tracking-normal text-ink">Advisor</h2>
            <p className="mt-1 text-sm leading-6 text-slate-500">
              Ask about your dashboard numbers and how they were worked out.
            </p>
          </div>
          <MessageSquareText className="text-cobalt" size={22} aria-hidden="true" />
        </div>

        <form className="grid gap-3" onSubmit={submitQuestion}>
          <label className="grid gap-2 text-sm font-medium text-slate-600">
            Question
            <textarea
              className="min-h-28 resize-y rounded-md border border-slate-200 bg-white px-3 py-3 text-sm leading-6 text-ink outline-none focus:border-cobalt"
              value={draftQuestion}
              onChange={(event) => setDraftQuestion(event.target.value)}
            />
          </label>
          <button
            className="focus-ring inline-flex h-11 items-center justify-center gap-2 rounded-md bg-ink px-4 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
            disabled={disabled || status === "loading" || !draftQuestion.trim()}
            type="submit"
          >
            {status === "loading" ? <LoaderCircle className="animate-spin" size={18} aria-hidden="true" /> : <Send size={18} aria-hidden="true" />}
            Ask advisor
          </button>
        </form>

        <div className="mt-5 grid gap-2">
          <p className="text-xs font-semibold uppercase text-slate-500">Suggested questions</p>
          <div className="flex flex-wrap gap-2">
            {suggestedQuestions.map((question) => (
              <button
                key={question}
                className="focus-ring inline-flex min-h-9 items-center rounded-md border border-slate-200 px-3 py-2 text-left text-xs font-semibold text-slate-600"
                type="button"
                onClick={() => {
                  setDraftQuestion(question);
                  if (!disabled && status !== "loading") onAsk(question);
                }}
              >
                {question}
              </button>
            ))}
          </div>
        </div>

        {status === "error" ? (
          <div className="mt-5 rounded-md border border-rose/30 bg-rose-50 p-4 text-sm text-rose">
            {errorMessage || "The advisor could not answer this question."}
          </div>
        ) : null}
      </section>

      <section className="rounded-md border border-slate-200 bg-panel p-5 shadow-soft">
        <div className="mb-5 flex items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold tracking-normal text-ink">Answer</h2>
            <p className="text-sm text-slate-500">
              {answer ? `Confidence: ${answer.confidence}` : "No advisor answer yet"}
            </p>
          </div>
          {answer ? (
            <CheckCircle2 className={confidenceTone(answer.confidence)} size={22} aria-hidden="true" />
          ) : (
            <BookOpen className="text-cobalt" size={22} aria-hidden="true" />
          )}
        </div>

        {status === "loading" ? (
          <div className="flex items-center gap-3 rounded-md border border-slate-200 p-4 text-sm font-semibold text-slate-600">
            <LoaderCircle className="animate-spin text-cobalt" size={18} aria-hidden="true" />
            Reading your figures and the background behind them
          </div>
        ) : null}

        {!answer && status !== "loading" ? (
          <div className="rounded-md border border-dashed border-slate-300 p-5 text-sm leading-6 text-slate-500">
            Ask a question to get an answer based on your own figures, with sources and anything still missing.
          </div>
        ) : null}

        {answer ? (
          <div className="grid gap-5">
            <div className="rounded-md border border-slate-200 p-4">
              <p className="text-sm leading-6 text-slate-700">{answer.answer}</p>
            </div>

            {answer.summary_bullets.length > 0 ? (
              <div>
                <h3 className="text-sm font-semibold uppercase text-slate-500">Key points</h3>
                <ul className="mt-3 grid gap-2 text-sm text-slate-700">
                  {answer.summary_bullets.map((item) => (
                    <li key={item} className="rounded-md border border-slate-200 p-3">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {answer.missing_data.length > 0 ? (
              <div>
                <h3 className="text-sm font-semibold uppercase text-slate-500">Missing data</h3>
                <div className="mt-3 grid gap-3">
                  {answer.missing_data.slice(0, 5).map((item) => (
                    <div key={item.key} className="rounded-md border border-dashed border-amber/50 bg-amber/5 p-4">
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <CircleAlert className="text-amber" size={17} aria-hidden="true" />
                            <p className="text-sm font-semibold text-ink">{item.label}</p>
                          </div>
                          <p className="mt-1 text-xs leading-5 text-slate-600">{item.impact}</p>
                        </div>
                        <button
                          className="focus-ring inline-flex h-9 items-center justify-center rounded-md border border-slate-200 bg-white px-3 text-xs font-semibold text-slate-600"
                          type="button"
                          onClick={() => onResolveMissing(item)}
                        >
                          {missingButtonLabel(item)}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}

            {answer.citations.length > 0 ? (
              <div>
                <h3 className="text-sm font-semibold uppercase text-slate-500">Citations</h3>
                <div className="mt-3 flex flex-wrap gap-2">
                  {citationLabels(answer.citations).map((label) => (
                    <span
                      key={label}
                      className="rounded-sm bg-blue-50 px-2 py-1 text-xs font-semibold text-cobalt"
                    >
                      {label}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}

            {answer.used_numbers.length > 0 ? (
              <div>
                <h3 className="text-sm font-semibold uppercase text-slate-500">Numbers used</h3>
                <div className="mt-3 grid gap-2 text-xs text-slate-600 sm:grid-cols-2">
                  {answer.used_numbers.map((item) => (
                    <div key={item} className="rounded-md border border-slate-200 p-3">
                      {item}
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        ) : null}
      </section>

      {answer?.retrieved_chunks.length ? (
        <section className="rounded-md border border-slate-200 bg-panel p-5 shadow-soft lg:col-span-2">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold tracking-normal text-ink">Where this came from</h2>
              <p className="text-sm text-slate-500">Background used to explain this answer</p>
            </div>
            <BookOpen className="text-teal" size={22} aria-hidden="true" />
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            {answer.retrieved_chunks.slice(0, 4).map((chunk) => (
              <article key={chunk.id} className="rounded-md border border-slate-200 p-4">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-sm font-semibold text-ink">{chunk.source_label}</h3>
                </div>
                <p className="mt-3 line-clamp-4 text-xs leading-5 text-slate-600">{chunk.body}</p>
              </article>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
