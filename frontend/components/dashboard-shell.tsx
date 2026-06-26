"use client";

import { useState } from "react";
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  Banknote,
  Gauge,
  Home,
  PiggyBank,
  ReceiptText,
  Upload
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import type { CategorySpend, InflationImpact, Metric } from "@/types/finscope";
import { uploadTransactions } from "@/lib/api";

const metrics: Metric[] = [
  { label: "Monthly income", value: "GBP 3,240", delta: "+2.1%", tone: "good" },
  { label: "Monthly spend", value: "GBP 2,415", delta: "-4.8%", tone: "good" },
  { label: "Disposable", value: "GBP 825", delta: "+11.2%", tone: "good" },
  { label: "Health score", value: "74", delta: "Stable", tone: "watch" }
];

const categorySpend: CategorySpend[] = [
  { category: "Groceries", spend: 410, forecast: 442 },
  { category: "Housing", spend: 1080, forecast: 1080 },
  { category: "Transport", spend: 165, forecast: 188 },
  { category: "Eating out", spend: 225, forecast: 214 },
  { category: "Bills", spend: 285, forecast: 302 },
  { category: "Subscriptions", spend: 54, forecast: 54 }
];

const inflationImpact: InflationImpact[] = [
  { category: "Food", personal: 4.8, national: 3.9 },
  { category: "Housing", personal: 5.2, national: 4.4 },
  { category: "Transport", personal: 2.1, national: 2.8 },
  { category: "Energy", personal: 3.6, national: 3.2 }
];

const healthRows = [
  { name: "Savings rate", score: 73 },
  { name: "Housing burden", score: 68 },
  { name: "Debt load", score: 91 },
  { name: "Emergency fund", score: 62 }
];

function toneClass(tone: Metric["tone"]) {
  if (tone === "good") return "text-teal";
  if (tone === "risk") return "text-rose";
  if (tone === "watch") return "text-amber";
  return "text-slate-500";
}

export function DashboardShell() {
  const [uploadStatus, setUploadStatus] = useState<{
    state: "idle" | "loading" | "success" | "error";
    message: string;
  }>({ state: "idle", message: "" });

  async function handleUpload(file: File | undefined) {
    if (!file) return;

    setUploadStatus({ state: "loading", message: "Reading CSV" });
    try {
      const result = await uploadTransactions(file);
      setUploadStatus({
        state: "success",
        message: `${result.rows} rows, GBP ${Number(result.total_spend).toLocaleString()} spend`
      });
    } catch (error) {
      setUploadStatus({
        state: "error",
        message: error instanceof Error ? error.message : "Upload failed"
      });
    }
  }

  return (
    <main className="min-h-screen bg-paper">
      <header className="border-b border-slate-200 bg-panel">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-5 py-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-normal text-cobalt">FinScope UK</p>
            <h1 className="mt-1 text-2xl font-semibold tracking-normal text-ink sm:text-3xl">
              Personal finance dashboard
            </h1>
          </div>
          <div className="flex flex-col items-start gap-2 sm:items-end">
            <label className="focus-ring inline-flex h-11 cursor-pointer items-center justify-center gap-2 rounded-md bg-ink px-4 text-sm font-semibold text-white shadow-soft transition hover:bg-slate-800">
              <Upload size={18} aria-hidden="true" />
              <span>Upload CSV</span>
              <input
                className="sr-only"
                type="file"
                accept=".csv"
                onChange={(event) => void handleUpload(event.target.files?.[0])}
              />
            </label>
            {uploadStatus.state !== "idle" ? (
              <p
                className={`text-sm font-medium ${
                  uploadStatus.state === "error" ? "text-rose" : "text-slate-600"
                }`}
              >
                {uploadStatus.message}
              </p>
            ) : null}
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-5 px-5 py-6 lg:grid-cols-[1.6fr_1fr]">
        <section className="grid gap-5">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {metrics.map((metric) => (
              <div key={metric.label} className="rounded-md border border-slate-200 bg-panel p-4 shadow-soft">
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm font-medium text-slate-500">{metric.label}</p>
                  {metric.tone === "good" ? (
                    <ArrowUpRight className="text-teal" size={18} aria-hidden="true" />
                  ) : (
                    <ArrowDownRight className={toneClass(metric.tone)} size={18} aria-hidden="true" />
                  )}
                </div>
                <p className="mt-3 text-2xl font-semibold tracking-normal text-ink">{metric.value}</p>
                <p className={`mt-1 text-sm font-medium ${toneClass(metric.tone)}`}>{metric.delta}</p>
              </div>
            ))}
          </div>

          <section className="rounded-md border border-slate-200 bg-panel p-5 shadow-soft">
            <div className="mb-5 flex items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold tracking-normal text-ink">Spending and forecast</h2>
                <p className="text-sm text-slate-500">Current month against next-month baseline</p>
              </div>
              <ReceiptText className="text-cobalt" size={22} aria-hidden="true" />
            </div>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={categorySpend} margin={{ left: 0, right: 8, top: 8, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="category" tickLine={false} axisLine={false} />
                  <YAxis tickLine={false} axisLine={false} />
                  <Tooltip />
                  <Bar dataKey="spend" fill="#2558a5" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="forecast" fill="#0f766e" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="rounded-md border border-slate-200 bg-panel p-5 shadow-soft">
            <div className="mb-5 flex items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold tracking-normal text-ink">Cost-of-living impact</h2>
                <p className="text-sm text-slate-500">Personal category mix against national releases</p>
              </div>
              <Activity className="text-rose" size={22} aria-hidden="true" />
            </div>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={inflationImpact} margin={{ left: 0, right: 8, top: 8, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="category" tickLine={false} axisLine={false} />
                  <YAxis tickLine={false} axisLine={false} />
                  <Tooltip />
                  <Line type="monotone" dataKey="personal" stroke="#be123c" strokeWidth={3} dot />
                  <Line type="monotone" dataKey="national" stroke="#b7791f" strokeWidth={3} dot />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>
        </section>

        <aside className="grid content-start gap-5">
          <section className="rounded-md border border-slate-200 bg-panel p-5 shadow-soft">
            <div className="mb-5 flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold tracking-normal text-ink">Financial health</h2>
              <Gauge className="text-teal" size={22} aria-hidden="true" />
            </div>
            <div className="flex items-end gap-3">
              <span className="text-6xl font-semibold tracking-normal text-ink">74</span>
              <span className="pb-2 text-sm font-semibold text-amber">Stable</span>
            </div>
            <div className="mt-6 grid gap-4">
              {healthRows.map((row) => (
                <div key={row.name}>
                  <div className="mb-2 flex items-center justify-between text-sm">
                    <span className="font-medium text-slate-600">{row.name}</span>
                    <span className="font-semibold text-ink">{row.score}</span>
                  </div>
                  <div className="h-2 rounded-sm bg-slate-100">
                    <div className="h-2 rounded-sm bg-teal" style={{ width: `${row.score}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-md border border-slate-200 bg-panel p-5 shadow-soft">
            <div className="mb-4 flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold tracking-normal text-ink">Pressure points</h2>
              <Home className="text-cobalt" size={22} aria-hidden="true" />
            </div>
            <div className="grid gap-3">
              <div className="flex items-center justify-between rounded-md border border-slate-200 p-3">
                <span className="text-sm font-medium text-slate-600">Rent-to-income</span>
                <span className="text-sm font-semibold text-ink">29%</span>
              </div>
              <div className="flex items-center justify-between rounded-md border border-slate-200 p-3">
                <span className="text-sm font-medium text-slate-600">Subscription leakage</span>
                <span className="text-sm font-semibold text-ink">GBP 54</span>
              </div>
              <div className="flex items-center justify-between rounded-md border border-slate-200 p-3">
                <span className="text-sm font-medium text-slate-600">Food inflation gap</span>
                <span className="text-sm font-semibold text-rose">+0.9 pp</span>
              </div>
            </div>
          </section>

          <section className="rounded-md border border-slate-200 bg-panel p-5 shadow-soft">
            <div className="mb-4 flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold tracking-normal text-ink">Scenario snapshot</h2>
              <Banknote className="text-amber" size={22} aria-hidden="true" />
            </div>
            <div className="grid gap-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-slate-600">Rent +8%</span>
                <span className="font-semibold text-ink">GBP 86/month</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-600">Food +10%</span>
                <span className="font-semibold text-ink">GBP 41/month</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-600">Bank Rate +0.25 pp</span>
                <span className="font-semibold text-ink">GBP 7/month</span>
              </div>
            </div>
          </section>

          <section className="rounded-md border border-slate-200 bg-panel p-5 shadow-soft">
            <div className="mb-4 flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold tracking-normal text-ink">Next actions</h2>
              <PiggyBank className="text-teal" size={22} aria-hidden="true" />
            </div>
            <ul className="grid gap-3 text-sm text-slate-600">
              <li>Move GBP 150 to emergency savings after payday.</li>
              <li>Review duplicate streaming subscriptions.</li>
              <li>Set grocery alert at GBP 440 for next month.</li>
            </ul>
          </section>
        </aside>
      </div>
    </main>
  );
}
