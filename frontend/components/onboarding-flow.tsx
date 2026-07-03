"use client";

import { FormEvent, useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, CheckCircle2, Gauge } from "lucide-react";

import { emptyProfile, profileFieldGroups } from "@/components/profile-form";
import type { OnboardingProfile } from "@/types/finscope";

type OnboardingFlowProps = {
  onReady: (profile: OnboardingProfile, name: string) => void;
};

const nameCacheKey = "finscope:onboarding-name";
const nameCacheTtlMs = 1000 * 60 * 60 * 6;

function readCachedName() {
  if (typeof window === "undefined") return "";

  try {
    const cached = window.sessionStorage.getItem(nameCacheKey);
    if (!cached) return "";

    const parsed = JSON.parse(cached) as { value?: string; savedAt?: number };
    if (!parsed.value || !parsed.savedAt || Date.now() - parsed.savedAt > nameCacheTtlMs) {
      window.sessionStorage.removeItem(nameCacheKey);
      return "";
    }

    return parsed.value;
  } catch {
    window.sessionStorage.removeItem(nameCacheKey);
    return "";
  }
}

function cacheName(name: string) {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(nameCacheKey, JSON.stringify({ value: name, savedAt: Date.now() }));
}

function profileFieldValue(value: number) {
  return value > 0 ? String(value) : "";
}

function parseProfileFieldValue(value: string) {
  if (value.trim() === "") return 0;
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 0;
}

export function OnboardingFlow({ onReady }: OnboardingFlowProps) {
  const [profile, setProfile] = useState<OnboardingProfile>(emptyProfile);
  const [name, setName] = useState("");
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    const cachedName = readCachedName();
    if (!cachedName) return;

    setName(cachedName);
    setStepIndex(1);
  }, []);

  const trimmedName = name.trim();
  const totalSteps = profileFieldGroups.length + 1;
  const progress = ((stepIndex + 1) / totalSteps) * 100;
  const group = profileFieldGroups[stepIndex - 1];
  const isNameStep = stepIndex === 0;
  const isFinalStep = stepIndex === totalSteps - 1;

  function goNext() {
    if (isNameStep) {
      if (!trimmedName) return;
      cacheName(trimmedName);
      setStepIndex(1);
      return;
    }

    if (isFinalStep) {
      onReady(profile, trimmedName || "there");
      return;
    }

    setStepIndex((current) => current + 1);
  }

  function goBack() {
    setStepIndex((current) => Math.max(current - 1, 0));
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    goNext();
  }

  return (
    <main className="grid min-h-screen place-items-center bg-paper px-5 py-8">
      <section
        aria-labelledby="onboarding-title"
        className="grid w-full max-w-3xl gap-6 rounded-md border border-slate-200 bg-panel p-5 shadow-soft sm:p-6"
        role="dialog"
      >
        <div className="flex items-start gap-3">
          <Gauge className="mt-1 shrink-0 text-cobalt" size={26} aria-hidden="true" />
          <div>
            <p className="text-sm font-semibold uppercase tracking-normal text-cobalt">FinScope UK</p>
            <h1 id="onboarding-title" className="mt-1 text-2xl font-semibold tracking-normal text-ink">
              {isNameStep ? "What's your name?" : `Hello ${trimmedName || "there"}, let's set ${group.title.toLowerCase()}`}
            </h1>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              {isNameStep
                ? "I use this only to make the setup feel less anonymous while this browser session is active."
                : group.intro}
            </p>
          </div>
        </div>

        <div className="grid gap-2">
          <div className="flex items-center justify-between text-xs font-semibold uppercase text-slate-500">
            <span>Step {stepIndex + 1} of {totalSteps}</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="h-2 rounded-sm bg-slate-100">
            <div className="h-2 rounded-sm bg-cobalt" style={{ width: `${progress}%` }} />
          </div>
        </div>

        <form className="grid gap-6" onSubmit={handleSubmit}>
          {isNameStep ? (
            <label className="grid gap-2 text-sm font-medium text-slate-600">
              Name
              <input
                autoComplete="given-name"
                autoFocus
                className="h-12 rounded-md border border-slate-200 bg-white px-3 text-base text-ink outline-none focus:border-cobalt"
                placeholder="Abdullah"
                type="text"
                value={name}
                onChange={(event) => setName(event.target.value)}
              />
              <span className="text-xs font-normal leading-5 text-slate-500">
                I cache it in this tab for a few hours, then ask again.
              </span>
            </label>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {group.fields.map((field) => (
                <label key={field.key} className="grid gap-2 text-sm font-medium text-slate-600">
                  {field.label}
                  <div className="flex h-11 items-center rounded-md border border-slate-200 bg-white focus-within:border-cobalt">
                    <input
                      className="min-w-0 flex-1 bg-transparent px-3 text-ink outline-none"
                      min="0"
                      placeholder={field.placeholder}
                      step={field.key === "averageDebtApr" ? "0.1" : "1"}
                      type="number"
                      value={profileFieldValue(profile[field.key])}
                      onChange={(event) =>
                        setProfile((current) => ({
                          ...current,
                          [field.key]: parseProfileFieldValue(event.target.value)
                        }))
                      }
                    />
                    {field.suffix ? (
                      <span className="border-l border-slate-200 px-3 text-xs font-semibold text-slate-500">
                        {field.suffix}
                      </span>
                    ) : null}
                  </div>
                  <span className="text-xs font-normal leading-5 text-slate-500">{field.helper}</span>
                </label>
              ))}
            </div>
          )}

          <div className="flex flex-col-reverse gap-3 border-t border-slate-200 pt-5 sm:flex-row sm:items-center sm:justify-between">
            <button
              className="focus-ring inline-flex h-11 items-center justify-center gap-2 rounded-md border border-slate-200 px-4 text-sm font-semibold text-slate-600 disabled:cursor-not-allowed disabled:opacity-40"
              disabled={stepIndex === 0}
              type="button"
              onClick={goBack}
            >
              <ArrowLeft size={18} aria-hidden="true" />
              Back
            </button>
            <button
              className="focus-ring inline-flex h-11 items-center justify-center gap-2 rounded-md bg-ink px-4 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
              disabled={isNameStep && !trimmedName}
              type="submit"
            >
              {isFinalStep ? "Open dashboard" : "Continue"}
              {isFinalStep ? <CheckCircle2 size={18} aria-hidden="true" /> : <ArrowRight size={18} aria-hidden="true" />}
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}
