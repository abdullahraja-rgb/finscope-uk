"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  Banknote,
  CheckCircle2,
  CircleAlert,
  Gauge,
  Home,
  LoaderCircle,
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

import type {
  CategorySpend,
  DerivedHealthScoreResponse,
  ForecastResponse,
  InflationImpact,
  Metric,
  RateImpactResponse,
  Recommendation,
  TransactionPayload
} from "@/types/finscope";
import {
  calculateDerivedHealthScore,
  calculateForecast,
  calculatePersonalInflation,
  calculateRateImpact,
  getRecommendations,
  uploadTransactions
} from "@/lib/api";

const metrics: Metric[] = [
  { label: "Monthly income", value: "GBP 3,240", delta: "+2.1%", tone: "good" },
  { label: "Monthly spend", value: "GBP 2,415", delta: "-4.8%", tone: "good" },
  { label: "Disposable", value: "GBP 825", delta: "+11.2%", tone: "good" },
  { label: "Health score", value: "74", delta: "Stable", tone: "watch" }
];

const fallbackCategorySpend: CategorySpend[] = [
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

const demoInflationTransactions = [
  {
    date: "2026-06-01",
    description: "Tesco Superstore",
    amount: -410,
    category: "groceries"
  },
  {
    date: "2026-06-01",
    description: "Rent Payment",
    amount: -1080,
    category: "housing"
  },
  {
    date: "2026-06-03",
    description: "TfL Travel Charge",
    amount: -165,
    category: "transport"
  },
  {
    date: "2026-06-04",
    description: "Deliveroo",
    amount: -225,
    category: "eating_out"
  },
  {
    date: "2026-06-08",
    description: "Octopus Energy",
    amount: -285,
    category: "utilities"
  },
  {
    date: "2026-06-11",
    description: "Netflix",
    amount: -54,
    category: "subscriptions"
  }
];

const demoHealthTransactions = [
  {
    date: "2026-06-25",
    description: "Salary Payroll",
    amount: 3240,
    category: "income"
  },
  ...demoInflationTransactions
];

const forecastMonths = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"];

const demoForecastTransactions: TransactionPayload[] = forecastMonths.flatMap((month, index) => [
  {
    date: `${month}-03`,
    description: "Tesco Superstore",
    amount: -(390 + index * 8),
    category: "groceries"
  },
  {
    date: `${month}-01`,
    description: "Rent Payment",
    amount: -1080,
    category: "housing"
  },
  {
    date: `${month}-05`,
    description: "TfL Travel Charge",
    amount: -(145 + index * 4),
    category: "transport"
  },
  {
    date: `${month}-10`,
    description: "Deliveroo",
    amount: -(200 + index * 5),
    category: "eating_out"
  },
  {
    date: `${month}-08`,
    description: "Octopus Energy",
    amount: -(260 + index * 6),
    category: "utilities"
  },
  {
    date: `${month}-11`,
    description: "Netflix",
    amount: -54,
    category: "subscriptions"
  }
]);

const fallbackRateImpact: RateImpactResponse = {
  current_bank_rate_pct: 3.75,
  scenario_bank_rate_pct: 4,
  bank_rate_change_pct_points: 0.25,
  effective_rate_change_pct_points: 0.25,
  monthly_net_cashflow_delta: -27,
  annual_net_cashflow_delta: -324,
  lines: [
    {
      name: "Repayment mortgage",
      monthly_delta: -28,
      annual_delta: -336,
      note: "Negative means the monthly repayment rises."
    },
    {
      name: "Savings interest",
      monthly_delta: 1,
      annual_delta: 12,
      note: "Positive means the savings balance earns more interest."
    }
  ],
  notes: []
};

const healthRows = [
  { name: "Savings rate", score: 73 },
  { name: "Housing burden", score: 68 },
  { name: "Debt load", score: 91 },
  { name: "Emergency fund", score: 62 }
];

const fallbackHealth: DerivedHealthScoreResponse = {
  score: 74,
  band: "Stable",
  components: healthRows.map((row) => ({
    name: row.name,
    score: row.score,
    weight: 0.25,
    note: ""
  })),
  monthly_income: 3240,
  monthly_spend: 2415,
  savings_rate: 0.2546,
  rent_to_income: 0.3333,
  emergency_fund_months: 2.5,
  spending_volatility: 0,
  benchmarks: [],
  notes: []
};

const fallbackRecommendations: Recommendation[] = [
  {
    title: "Build the emergency buffer first",
    detail: "Emergency savings cover 2.5 months of spend.",
    action: "Move GBP 150 to savings after payday until this reaches three months.",
    priority: "high",
    source: "Health score"
  },
  {
    title: "Review subscriptions",
    detail: "Recurring payments are visible in the monthly spend mix.",
    action: "Cancel one low-use subscription before the next billing date.",
    priority: "medium",
    source: "Health score"
  },
  {
    title: "Set a grocery alert",
    detail: "The forecast expects groceries to stay near GBP 440 next month.",
    action: "Use the forecast as next month's alert level.",
    priority: "medium",
    source: "Forecast"
  }
];

function toneClass(tone: Metric["tone"]) {
  if (tone === "good") return "text-teal";
  if (tone === "risk") return "text-rose";
  if (tone === "watch") return "text-amber";
  return "text-slate-500";
}

function shortCategory(category: string) {
  return category
    .replace("Food and non-alcoholic beverages", "Food")
    .replace("Housing, water, electricity, gas and other fuels (Inc OOH)", "Housing")
    .replace("Restaurants and hotels", "Eating out")
    .replace("Recreation and culture", "Subscriptions");
}

function displayCategory(category: string) {
  return category
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function latestMonthSpend(transactions: TransactionPayload[]) {
  const expenseMonths = transactions
    .filter((transaction) => transaction.amount < 0)
    .map((transaction) => transaction.date.slice(0, 7))
    .sort();
  const latestMonth = expenseMonths[expenseMonths.length - 1];
  const totals: Record<string, number> = {};

  for (const transaction of transactions) {
    if (transaction.amount >= 0 || transaction.date.slice(0, 7) !== latestMonth) continue;
    const category = transaction.category ?? "uncategorised";
    totals[category] = (totals[category] ?? 0) + Math.abs(transaction.amount);
  }

  return totals;
}

function forecastRowsFromResponse(forecast: ForecastResponse, transactions: TransactionPayload[]) {
  const currentSpend = latestMonthSpend(transactions);
  return forecast.forecasts.slice(0, 6).map((point) => ({
    category: displayCategory(point.category),
    spend: Math.round(currentSpend[point.category] ?? 0),
    forecast: Math.round(point.expected_spend)
  }));
}

type UploadState = {
  state: "idle" | "loading" | "success" | "error";
  message: string;
};

type UploadSummary = {
  rows: number;
  totalSpend: number;
  categoryCount: number;
  forecastCount: number;
  healthScore: number | null;
  personalInflation: number | null;
  notes: string[];
};

const uploadStateStyles: Record<UploadState["state"], string> = {
  idle: "border-slate-200 bg-panel text-slate-600",
  loading: "border-cobalt/30 bg-blue-50 text-cobalt",
  success: "border-teal/30 bg-emerald-50 text-teal",
  error: "border-rose/30 bg-rose-50 text-rose"
};

function uploadIcon(state: UploadState["state"]) {
  if (state === "loading") return <LoaderCircle className="animate-spin" size={18} aria-hidden="true" />;
  if (state === "success") return <CheckCircle2 size={18} aria-hidden="true" />;
  if (state === "error") return <CircleAlert size={18} aria-hidden="true" />;
  return <Upload size={18} aria-hidden="true" />;
}

function uploadSummaryFromResult(result: Awaited<ReturnType<typeof uploadTransactions>>): UploadSummary {
  const categories = new Set(
    result.transactions.map((transaction) => transaction.category ?? transaction.predicted_category)
  );

  return {
    rows: result.rows,
    totalSpend: result.total_spend,
    categoryCount: categories.size,
    forecastCount: result.forecast.forecasts.length,
    healthScore: result.health_score?.score ?? null,
    personalInflation: result.personal_inflation?.personal_inflation_pct ?? null,
    notes: result.notes
  };
}

function priorityTone(priority: string) {
  if (priority === "high") return "text-rose";
  if (priority === "medium") return "text-amber";
  return "text-teal";
}

export function DashboardShell() {
  const [uploadStatus, setUploadStatus] = useState<UploadState>({ state: "idle", message: "" });
  const [uploadSummary, setUploadSummary] = useState<UploadSummary | null>(null);
  const [costOfLiving, setCostOfLiving] = useState<{
    period: string;
    personalRate: number;
    nationalRate: number;
    chart: InflationImpact[];
  }>({
    period: "Demo",
    personalRate: 4.1,
    nationalRate: 3.9,
    chart: inflationImpact
  });
  const [rateImpact, setRateImpact] = useState<RateImpactResponse>(fallbackRateImpact);
  const [healthScore, setHealthScore] = useState<DerivedHealthScoreResponse>(fallbackHealth);
  const [forecastRows, setForecastRows] = useState<CategorySpend[]>(fallbackCategorySpend);
  const [forecastPeriod, setForecastPeriod] = useState("Demo");
  const [recommendations, setRecommendations] = useState<Recommendation[]>(fallbackRecommendations);

  useEffect(() => {
    let isMounted = true;

    async function loadLiveCostOfLiving() {
      try {
        const [inflationResponse, rateResponse, healthResponse, forecastResponse] = await Promise.all([
          calculatePersonalInflation(demoInflationTransactions),
          calculateRateImpact({
            savings_balance: 6000,
            variable_debt_balance: 2400,
            mortgage_balance: 180000,
            mortgage_years_remaining: 22,
            current_mortgage_rate_pct: 5,
            bank_rate_change_pct_points: 0.25
          }),
          calculateDerivedHealthScore({
            transactions: demoHealthTransactions,
            liquid_savings: 6000,
            monthly_debt_payment: 120
          }),
          calculateForecast(demoForecastTransactions)
        ]);
        if (!isMounted) return;

        setCostOfLiving({
          period: inflationResponse.period,
          personalRate: inflationResponse.personal_inflation_pct,
          nationalRate: inflationResponse.national_inflation_pct,
          chart: inflationResponse.categories
            .filter((category) => category.annual_change_pct !== null)
            .slice(0, 6)
            .map((category) => ({
              category: shortCategory(category.ons_category ?? category.app_category),
              personal: category.annual_change_pct ?? 0,
              national: inflationResponse.national_inflation_pct
            }))
        });
        setRateImpact(rateResponse);
        setHealthScore(healthResponse);
        setForecastPeriod(forecastResponse.period);
        setForecastRows(forecastRowsFromResponse(forecastResponse, demoForecastTransactions));
        const recommendationResponse = await getRecommendations({
          forecast: forecastResponse,
          personal_inflation: inflationResponse,
          health_score: healthResponse,
          rate_impact: rateResponse
        });
        if (!isMounted) return;
        setRecommendations(recommendationResponse.recommendations);
      } catch {
        if (!isMounted) return;
      }
    }

    void loadLiveCostOfLiving();

    return () => {
      isMounted = false;
    };
  }, []);

  async function handleUpload(file: File | undefined) {
    if (!file) return;

    setUploadStatus({ state: "loading", message: "Reading CSV" });
    setUploadSummary(null);
    try {
      const result = await uploadTransactions(file);
      setUploadStatus({
        state: "success",
        message: `${result.rows} rows, GBP ${Number(result.total_spend).toLocaleString()} spend`
      });
      setUploadSummary(uploadSummaryFromResult(result));

      if (result.forecast.forecasts.length > 0) {
        setForecastPeriod(result.forecast.period);
        setForecastRows(forecastRowsFromResponse(result.forecast, result.transactions));
      }

      if (result.personal_inflation) {
        setCostOfLiving({
          period: result.personal_inflation.period,
          personalRate: result.personal_inflation.personal_inflation_pct,
          nationalRate: result.personal_inflation.national_inflation_pct,
          chart: result.personal_inflation.categories
            .filter((category) => category.annual_change_pct !== null)
            .slice(0, 6)
            .map((category) => ({
              category: shortCategory(category.ons_category ?? category.app_category),
              personal: category.annual_change_pct ?? 0,
              national: result.personal_inflation?.national_inflation_pct ?? 0
            }))
        });
      }

      if (result.health_score) {
        setHealthScore(result.health_score);
      }

      if (result.recommendations.length > 0) {
        setRecommendations(result.recommendations);
      }
    } catch (error) {
      setUploadSummary(null);
      setUploadStatus({
        state: "error",
        message: error instanceof Error ? error.message : "Upload failed"
      });
    }
  }

  const mortgageImpact = rateImpact.lines.find((line) => line.name === "Repayment mortgage");
  const savingsImpact = rateImpact.lines.find((line) => line.name === "Savings interest");
  const debtImpact = rateImpact.lines.find((line) => line.name === "Variable debt cost");
  const dashboardMetrics = metrics.map((metric) =>
    metric.label === "Health score"
      ? { ...metric, value: Math.round(healthScore.score).toString(), delta: healthScore.band }
      : metric
  );
  const housingBenchmark = healthScore.benchmarks.find((benchmark) => benchmark.coicop_code === "04");

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
                onChange={(event) => {
                  void handleUpload(event.target.files?.[0]);
                  event.currentTarget.value = "";
                }}
              />
            </label>
          </div>
        </div>
      </header>

      {uploadStatus.state !== "idle" ? (
        <section
          className={`border-b ${uploadStateStyles[uploadStatus.state]}`}
          aria-live="polite"
          aria-atomic="true"
        >
          <div className="mx-auto grid max-w-7xl gap-3 px-5 py-3 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center">
            <div className="flex min-w-0 items-center gap-2 text-sm font-semibold">
              {uploadIcon(uploadStatus.state)}
              <span className="truncate">{uploadStatus.message}</span>
            </div>
            {uploadSummary ? (
              <dl className="grid grid-cols-2 gap-x-5 gap-y-2 text-sm sm:grid-cols-3 lg:flex lg:items-center">
                <div>
                  <dt className="text-slate-500">Rows</dt>
                  <dd className="font-semibold text-ink">{uploadSummary.rows.toLocaleString()}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Spend</dt>
                  <dd className="font-semibold text-ink">
                    GBP {Math.round(uploadSummary.totalSpend).toLocaleString()}
                  </dd>
                </div>
                <div>
                  <dt className="text-slate-500">Categories</dt>
                  <dd className="font-semibold text-ink">{uploadSummary.categoryCount}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Forecasts</dt>
                  <dd className="font-semibold text-ink">{uploadSummary.forecastCount}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Health</dt>
                  <dd className="font-semibold text-ink">
                    {uploadSummary.healthScore === null ? "n/a" : Math.round(uploadSummary.healthScore)}
                  </dd>
                </div>
                <div>
                  <dt className="text-slate-500">Inflation</dt>
                  <dd className="font-semibold text-ink">
                    {uploadSummary.personalInflation === null
                      ? "n/a"
                      : `${uploadSummary.personalInflation.toFixed(1)}%`}
                  </dd>
                </div>
              </dl>
            ) : null}
          </div>
          {uploadSummary?.notes.length ? (
            <div className="mx-auto max-w-7xl px-5 pb-3 text-sm text-slate-600">{uploadSummary.notes[0]}</div>
          ) : null}
        </section>
      ) : null}

      <div className="mx-auto grid max-w-7xl gap-5 px-5 py-6 lg:grid-cols-[1.6fr_1fr]">
        <section className="grid gap-5">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {dashboardMetrics.map((metric) => (
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
                <p className="text-sm text-slate-500">Current month against {forecastPeriod} forecast</p>
              </div>
              <ReceiptText className="text-cobalt" size={22} aria-hidden="true" />
            </div>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={forecastRows} margin={{ left: 0, right: 8, top: 8, bottom: 0 }}>
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
                <p className="text-sm text-slate-500">
                  CPIH {costOfLiving.period} - personal {costOfLiving.personalRate.toFixed(1)}% vs UK{" "}
                  {costOfLiving.nationalRate.toFixed(1)}%
                </p>
              </div>
              <Activity className="text-rose" size={22} aria-hidden="true" />
            </div>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={costOfLiving.chart} margin={{ left: 0, right: 8, top: 8, bottom: 0 }}>
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
              <span className="text-6xl font-semibold tracking-normal text-ink">
                {Math.round(healthScore.score)}
              </span>
              <span className="pb-2 text-sm font-semibold text-amber">{healthScore.band}</span>
            </div>
            <div className="mt-6 grid gap-4">
              {healthScore.components.slice(0, 4).map((component) => (
                <div key={component.name}>
                  <div className="mb-2 flex items-center justify-between text-sm">
                    <span className="font-medium text-slate-600">{component.name}</span>
                    <span className="font-semibold text-ink">{Math.round(component.score)}</span>
                  </div>
                  <div className="h-2 rounded-sm bg-slate-100">
                    <div className="h-2 rounded-sm bg-teal" style={{ width: `${component.score}%` }} />
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
                <span className="text-sm font-semibold text-ink">
                  {Math.round(healthScore.rent_to_income * 100)}%
                </span>
              </div>
              <div className="flex items-center justify-between rounded-md border border-slate-200 p-3">
                <span className="text-sm font-medium text-slate-600">Emergency fund</span>
                <span className="text-sm font-semibold text-ink">
                  {healthScore.emergency_fund_months.toFixed(1)} months
                </span>
              </div>
              <div className="flex items-center justify-between rounded-md border border-slate-200 p-3">
                <span className="text-sm font-medium text-slate-600">Housing vs ONS</span>
                <span className="text-sm font-semibold text-rose">
                  {housingBenchmark ? `${housingBenchmark.difference_pct_points.toFixed(1)} pp` : "n/a"}
                </span>
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
                <span className="text-slate-600">Mortgage impact</span>
                <span className="font-semibold text-ink">
                  GBP {Math.round(mortgageImpact?.monthly_delta ?? 0)}/month
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-600">Savings interest</span>
                <span className="font-semibold text-ink">
                  GBP +{Math.round(savingsImpact?.monthly_delta ?? 0)}/month
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-600">Variable debt</span>
                <span className="font-semibold text-ink">
                  GBP {Math.round(debtImpact?.monthly_delta ?? 0)}/month
                </span>
              </div>
              <div className="flex items-center justify-between border-t border-slate-200 pt-3">
                <span className="font-medium text-slate-600">
                  Bank Rate {rateImpact.current_bank_rate_pct.toFixed(2)}% to{" "}
                  {rateImpact.scenario_bank_rate_pct.toFixed(2)}%
                </span>
                <span className="font-semibold text-ink">
                  GBP {Math.round(rateImpact.monthly_net_cashflow_delta)}/month
                </span>
              </div>
            </div>
          </section>

          <section className="rounded-md border border-slate-200 bg-panel p-5 shadow-soft">
            <div className="mb-4 flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold tracking-normal text-ink">Next actions</h2>
              <PiggyBank className="text-teal" size={22} aria-hidden="true" />
            </div>
            <ul className="grid gap-3 text-sm text-slate-600">
              {recommendations.slice(0, 4).map((recommendation) => (
                <li key={`${recommendation.source}-${recommendation.title}`} className="grid gap-1">
                  <div className="flex items-start justify-between gap-3">
                    <span className="font-semibold text-ink">{recommendation.title}</span>
                    <span className={`text-xs font-semibold uppercase ${priorityTone(recommendation.priority)}`}>
                      {recommendation.priority}
                    </span>
                  </div>
                  <span>{recommendation.detail}</span>
                  <span className="font-medium text-slate-700">{recommendation.action}</span>
                </li>
              ))}
            </ul>
          </section>
        </aside>
      </div>
    </main>
  );
}
