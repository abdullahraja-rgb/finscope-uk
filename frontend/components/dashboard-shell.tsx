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
import type { LucideIcon } from "lucide-react";
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
  OnboardingProfile,
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
import { OnboardingFlow } from "@/components/onboarding-flow";

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

type DashboardView = "overview" | "spending" | "costs" | "net-worth" | "debt" | "goals" | "actions";

const dashboardViews: Array<{
  id: DashboardView;
  label: string;
  helper: string;
  icon: LucideIcon;
}> = [
  { id: "overview", label: "Overview", helper: "Cash flow and score", icon: Gauge },
  { id: "spending", label: "Spending", helper: "Monthly spend and forecast", icon: ReceiptText },
  { id: "costs", label: "Cost of living", helper: "Inflation and rate pressure", icon: Activity },
  { id: "net-worth", label: "Net worth", helper: "Assets and liabilities", icon: Banknote },
  { id: "debt", label: "Debt payoff", helper: "Balances and payoff time", icon: CircleAlert },
  { id: "goals", label: "Savings goals", helper: "Emergency and target progress", icon: PiggyBank },
  { id: "actions", label: "Next actions", helper: "Recommendations and scenario", icon: CheckCircle2 }
];

function formatGBP(value: number) {
  return `GBP ${Math.round(value).toLocaleString()}`;
}

function formatPercent(value: number, digits = 0) {
  return `${value.toFixed(digits)}%`;
}

function clampPercentage(value: number) {
  return Math.max(0, Math.min(100, value));
}

function progressPercentage(current: number, target: number) {
  if (target <= 0) return 100;
  return clampPercentage((current / target) * 100);
}

function formatMonths(months: number | null) {
  if (months === null) return "Not moving yet";
  if (months <= 0) return "Cleared";

  const years = Math.floor(months / 12);
  const remainingMonths = months % 12;

  if (years === 0) return `${remainingMonths} mo`;
  if (remainingMonths === 0) return `${years} yr`;
  return `${years} yr ${remainingMonths} mo`;
}

function payoffEstimate(balance: number, monthlyPayment: number, apr: number) {
  if (balance <= 0) return { months: 0, interest: 0 };
  if (monthlyPayment <= 0) return { months: null, interest: null };

  const monthlyRate = Math.max(apr, 0) / 100 / 12;
  if (monthlyRate === 0) {
    const months = Math.ceil(balance / monthlyPayment);
    return { months, interest: Math.max(months * monthlyPayment - balance, 0) };
  }

  if (monthlyPayment <= balance * monthlyRate) return { months: null, interest: null };

  const months = Math.ceil(-Math.log(1 - (monthlyRate * balance) / monthlyPayment) / Math.log(1 + monthlyRate));
  return { months, interest: Math.max(months * monthlyPayment - balance, 0) };
}

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

function demoSpendingTransactionsForProfile(profile: OnboardingProfile) {
  return demoInflationTransactions.map((transaction) =>
    transaction.category === "housing" ? { ...transaction, amount: -profile.rentOrMortgage } : transaction
  );
}

function demoHealthTransactionsForProfile(profile: OnboardingProfile) {
  const demoSpendingTransactions = demoSpendingTransactionsForProfile(profile);
  return [
    {
      date: "2026-06-25",
      description: "Salary Payroll",
      amount: profile.monthlyIncome,
      category: "income"
    },
    ...demoSpendingTransactions
  ];
}

export function DashboardShell() {
  const [activeProfile, setActiveProfile] = useState<OnboardingProfile | null>(null);
  const [activeView, setActiveView] = useState<DashboardView>("overview");
  const [dataMode, setDataMode] = useState<"demo" | "uploaded">("demo");
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
    if (!activeProfile) return;
    let isMounted = true;

    async function loadLiveCostOfLiving() {
      if (!activeProfile) return;

      const demoHealthTransactions = demoHealthTransactionsForProfile(activeProfile);
      const demoSpendingTransactions = demoSpendingTransactionsForProfile(activeProfile);
      const variableDebtBalance = activeProfile.creditCardBalance + activeProfile.loanBalance;
      try {
        const [inflationResponse, rateResponse, healthResponse, forecastResponse] = await Promise.all([
          calculatePersonalInflation(demoSpendingTransactions),
          calculateRateImpact({
            savings_balance: activeProfile.liquidSavings,
            variable_debt_balance: variableDebtBalance > 0 ? variableDebtBalance : activeProfile.monthlyDebtPayment * 20,
            mortgage_balance: activeProfile.mortgageBalance > 0 ? activeProfile.mortgageBalance : undefined,
            mortgage_years_remaining: 22,
            current_mortgage_rate_pct: 5,
            bank_rate_change_pct_points: 0.25
          }),
          calculateDerivedHealthScore({
            transactions: demoHealthTransactions,
            monthly_income: activeProfile.monthlyIncome,
            liquid_savings: activeProfile.liquidSavings,
            monthly_debt_payment: activeProfile.monthlyDebtPayment,
            rent_or_mortgage: activeProfile.rentOrMortgage
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
  }, [activeProfile]);

  async function handleUpload(file: File | undefined) {
    if (!file) return;

    setUploadStatus({ state: "loading", message: "Reading CSV" });
    setUploadSummary(null);
    try {
      const result = await uploadTransactions(file, activeProfile ?? undefined);
      setUploadStatus({
        state: "success",
        message: `${result.rows} rows, GBP ${Number(result.total_spend).toLocaleString()} spend`
      });
      setUploadSummary(uploadSummaryFromResult(result));
      setDataMode("uploaded");
      setActiveView("overview");

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
  const income = activeProfile?.monthlyIncome ?? fallbackHealth.monthly_income;
  const spend = healthScore.monthly_spend;
  const disposable = income - spend;
  const dashboardMetrics: Metric[] = [
    {
      label: "Monthly income",
      value: `GBP ${Math.round(income).toLocaleString()}`,
      delta: "From setup",
      tone: "neutral"
    },
    {
      label: "Monthly spend",
      value: `GBP ${Math.round(spend).toLocaleString()}`,
      delta: `${Math.round((spend / Math.max(income, 1)) * 100)}% of income`,
      tone: spend / Math.max(income, 1) < 0.85 ? "good" : "watch"
    },
    {
      label: "Disposable",
      value: `GBP ${Math.round(disposable).toLocaleString()}`,
      delta: disposable >= 0 ? "After spending" : "Overspent",
      tone: disposable >= 0 ? "good" : "risk"
    },
    {
      label: "Health score",
      value: Math.round(healthScore.score).toString(),
      delta: healthScore.band,
      tone: healthScore.score >= 80 ? "good" : healthScore.score >= 60 ? "watch" : "risk"
    }
  ];
  const housingBenchmark = healthScore.benchmarks.find((benchmark) => benchmark.coicop_code === "04");
  const dataModeLabel = dataMode === "uploaded" ? "Uploaded CSV" : "Demo baseline";
  const dataModeDetail =
    dataMode === "uploaded"
      ? "Spend, forecast, inflation, health score, and actions are using the latest CSV analysis."
      : "Spend, forecast, inflation, health score, and actions are using demo transactions until a CSV is uploaded.";
  const totalAssets =
    (activeProfile?.liquidSavings ?? 0) +
    (activeProfile?.investmentBalance ?? 0) +
    (activeProfile?.pensionBalance ?? 0) +
    (activeProfile?.propertyValue ?? 0);
  const consumerDebt = (activeProfile?.creditCardBalance ?? 0) + (activeProfile?.loanBalance ?? 0);
  const totalLiabilities = (activeProfile?.mortgageBalance ?? 0) + consumerDebt;
  const netWorth = totalAssets - totalLiabilities;
  const netWorthRows = [
    { label: "Cash savings", value: activeProfile?.liquidSavings ?? 0, tone: "text-teal" },
    { label: "Investments", value: activeProfile?.investmentBalance ?? 0, tone: "text-cobalt" },
    { label: "Pension", value: activeProfile?.pensionBalance ?? 0, tone: "text-amber" },
    { label: "Property", value: activeProfile?.propertyValue ?? 0, tone: "text-slate-600" },
    { label: "Mortgage", value: -(activeProfile?.mortgageBalance ?? 0), tone: "text-rose" },
    { label: "Cards and loans", value: -consumerDebt, tone: "text-rose" }
  ];
  const payoff = payoffEstimate(
    consumerDebt,
    activeProfile?.monthlyDebtPayment ?? 0,
    activeProfile?.averageDebtApr ?? 0
  );
  const monthlyDebtToIncome = ((activeProfile?.monthlyDebtPayment ?? 0) / Math.max(income, 1)) * 100;
  const interestOnlyPayment = consumerDebt * ((activeProfile?.averageDebtApr ?? 0) / 100 / 12);
  const emergencyProgress = progressPercentage(activeProfile?.liquidSavings ?? 0, activeProfile?.emergencyFundTarget ?? 0);
  const emergencyGap = Math.max((activeProfile?.emergencyFundTarget ?? 0) - (activeProfile?.liquidSavings ?? 0), 0);
  const goalStartingBalance = Math.max(
    (activeProfile?.liquidSavings ?? 0) - (activeProfile?.emergencyFundTarget ?? 0),
    0
  );
  const goalProgress = progressPercentage(goalStartingBalance, activeProfile?.savingsGoalTarget ?? 0);
  const goalGap = Math.max((activeProfile?.savingsGoalTarget ?? 0) - goalStartingBalance, 0);
  const monthlyGoalContribution = activeProfile?.monthlyGoalContribution ?? 0;
  const monthsToEmergency =
    emergencyGap <= 0 ? 0 : monthlyGoalContribution > 0 ? Math.ceil(emergencyGap / monthlyGoalContribution) : null;
  const monthsToGoal = goalGap <= 0 ? 0 : monthlyGoalContribution > 0 ? Math.ceil(goalGap / monthlyGoalContribution) : null;

  if (!activeProfile) {
    return <OnboardingFlow onReady={setActiveProfile} />;
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
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">{dataModeDetail}</p>
          </div>
          <div className="flex flex-col items-start gap-2 sm:items-end">
            <div className="flex flex-wrap justify-end gap-2">
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
              <button
                className="focus-ring inline-flex h-11 items-center justify-center gap-2 rounded-md border border-slate-200 px-4 text-sm font-semibold text-slate-600"
                type="button"
                onClick={() => {
                  setActiveProfile(null);
                  setActiveView("overview");
                  setDataMode("demo");
                  setUploadSummary(null);
                  setUploadStatus({ state: "idle", message: "" });
                }}
              >
                <Gauge size={18} aria-hidden="true" />
                Change details
              </button>
            </div>
            <p className="flex flex-wrap items-center justify-end gap-2 text-sm font-medium text-slate-500">
              <span
                className={`rounded-sm px-2 py-1 text-xs font-semibold uppercase ${
                  dataMode === "uploaded" ? "bg-emerald-50 text-teal" : "bg-blue-50 text-cobalt"
                }`}
              >
                {dataModeLabel}
              </span>
              <span>Income {formatGBP(activeProfile.monthlyIncome)}</span>
            </p>
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

      <nav className="border-b border-slate-200 bg-panel">
        <div className="mx-auto flex max-w-7xl gap-2 overflow-x-auto px-5 py-3">
          {dashboardViews.map((view) => {
            const ViewIcon = view.icon;
            const isActive = activeView === view.id;

            return (
              <button
                key={view.id}
                className={`focus-ring flex min-w-[160px] items-center gap-3 rounded-md border px-3 py-3 text-left transition ${
                  isActive
                    ? "border-ink bg-ink text-white"
                    : "border-slate-200 bg-white text-slate-600 hover:border-cobalt"
                }`}
                type="button"
                onClick={() => setActiveView(view.id)}
              >
                <ViewIcon size={19} aria-hidden="true" />
                <span className="grid gap-0.5">
                  <span className="text-sm font-semibold">{view.label}</span>
                  <span className={`text-xs ${isActive ? "text-white/70" : "text-slate-500"}`}>{view.helper}</span>
                </span>
              </button>
            );
          })}
        </div>
      </nav>

      {["overview", "spending", "costs", "actions"].includes(activeView) ? (
        <div
          className={`mx-auto grid max-w-7xl gap-5 px-5 py-6 ${
            activeView === "overview" || activeView === "costs" ? "lg:grid-cols-[1.6fr_1fr]" : "lg:grid-cols-1"
          }`}
        >
        <section className="grid gap-5">
          {activeView === "overview" ? (
            <>
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
                    <h2 className="text-lg font-semibold tracking-normal text-ink">Data status</h2>
                    <p className="text-sm text-slate-500">What the dashboard is using right now</p>
                  </div>
                  <ReceiptText className="text-cobalt" size={22} aria-hidden="true" />
                </div>
                <dl className="grid gap-3 text-sm sm:grid-cols-2">
                  <div className="rounded-md border border-slate-200 p-3">
                    <dt className="text-slate-500">Analysis source</dt>
                    <dd className="mt-1 font-semibold text-ink">{dataModeLabel}</dd>
                  </div>
                  <div className="rounded-md border border-slate-200 p-3">
                    <dt className="text-slate-500">Setup profile</dt>
                    <dd className="mt-1 font-semibold text-ink">{formatGBP(activeProfile.monthlyIncome)} income</dd>
                  </div>
                  <div className="rounded-md border border-slate-200 p-3">
                    <dt className="text-slate-500">CSV rows</dt>
                    <dd className="mt-1 font-semibold text-ink">
                      {uploadSummary ? uploadSummary.rows.toLocaleString() : "No upload yet"}
                    </dd>
                  </div>
                  <div className="rounded-md border border-slate-200 p-3">
                    <dt className="text-slate-500">Forecast period</dt>
                    <dd className="mt-1 font-semibold text-ink">{forecastPeriod}</dd>
                  </div>
                </dl>
                <p className="mt-4 text-sm leading-6 text-slate-600">{dataModeDetail}</p>
              </section>
            </>
          ) : null}

          {activeView === "spending" ? (
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
          ) : null}

          {activeView === "spending" ? (
            <section className="rounded-md border border-slate-200 bg-panel p-5 shadow-soft">
              <div className="mb-4 flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold tracking-normal text-ink">Category detail</h2>
                  <p className="text-sm text-slate-500">Spend and next-month expectation by category</p>
                </div>
                <Activity className="text-teal" size={22} aria-hidden="true" />
              </div>
              <div className="overflow-x-auto rounded-md border border-slate-200">
                <table className="min-w-full divide-y divide-slate-200 text-sm">
                  <thead className="bg-slate-50 text-left text-xs font-semibold uppercase text-slate-500">
                    <tr>
                      <th className="px-4 py-3">Category</th>
                      <th className="px-4 py-3">Current spend</th>
                      <th className="px-4 py-3">Forecast</th>
                      <th className="px-4 py-3">Change</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 bg-white">
                    {forecastRows.map((row) => {
                      const change = row.forecast - row.spend;

                      return (
                        <tr key={row.category}>
                          <td className="px-4 py-3 font-medium text-ink">{row.category}</td>
                          <td className="px-4 py-3 text-slate-600">{formatGBP(row.spend)}</td>
                          <td className="px-4 py-3 text-slate-600">{formatGBP(row.forecast)}</td>
                          <td className={`px-4 py-3 font-semibold ${change <= 0 ? "text-teal" : "text-amber"}`}>
                            {change >= 0 ? "+" : ""}
                            {formatGBP(change)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </section>
          ) : null}

          {activeView === "costs" ? (
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
          ) : null}
        </section>

        <aside className="grid content-start gap-5">
          {activeView === "overview" ? (
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
          ) : null}

          {activeView === "overview" || activeView === "costs" ? (
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
          ) : null}

          {activeView === "costs" || activeView === "actions" ? (
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
          ) : null}

          {activeView === "overview" || activeView === "actions" ? (
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
          ) : null}
        </aside>
        </div>
      ) : null}

      {activeView === "net-worth" ? (
        <div className="mx-auto grid max-w-7xl gap-5 px-5 py-6">
          <div className="grid gap-4 md:grid-cols-3">
            <section className="rounded-md border border-slate-200 bg-panel p-5 shadow-soft">
              <p className="text-sm font-medium text-slate-500">Total assets</p>
              <p className="mt-3 text-3xl font-semibold tracking-normal text-ink">{formatGBP(totalAssets)}</p>
            </section>
            <section className="rounded-md border border-slate-200 bg-panel p-5 shadow-soft">
              <p className="text-sm font-medium text-slate-500">Total liabilities</p>
              <p className="mt-3 text-3xl font-semibold tracking-normal text-rose">
                {formatGBP(totalLiabilities)}
              </p>
            </section>
            <section className="rounded-md border border-slate-200 bg-panel p-5 shadow-soft">
              <p className="text-sm font-medium text-slate-500">Net worth</p>
              <p className={`mt-3 text-3xl font-semibold tracking-normal ${netWorth >= 0 ? "text-teal" : "text-rose"}`}>
                {formatGBP(netWorth)}
              </p>
            </section>
          </div>

          <section className="rounded-md border border-slate-200 bg-panel p-5 shadow-soft">
            <div className="mb-5 flex items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold tracking-normal text-ink">Assets and liabilities</h2>
                <p className="text-sm text-slate-500">Setup balances grouped into the net-worth view</p>
              </div>
              <Banknote className="text-cobalt" size={22} aria-hidden="true" />
            </div>
            <div className="grid gap-4">
              {netWorthRows.map((row) => (
                <div key={row.label} className="grid gap-2">
                  <div className="flex items-center justify-between gap-3 text-sm">
                    <span className="font-medium text-slate-600">{row.label}</span>
                    <span className={`font-semibold ${row.tone}`}>{formatGBP(row.value)}</span>
                  </div>
                  <div className="h-3 rounded-sm bg-slate-100">
                    <div
                      className={`h-3 rounded-sm ${row.value >= 0 ? "bg-teal" : "bg-rose"}`}
                      style={{
                        width: `${progressPercentage(Math.abs(row.value), Math.max(totalAssets, totalLiabilities, 1))}%`
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      ) : null}

      {activeView === "debt" ? (
        <div className="mx-auto grid max-w-7xl gap-5 px-5 py-6 lg:grid-cols-[1fr_1fr]">
          <section className="rounded-md border border-slate-200 bg-panel p-5 shadow-soft">
            <div className="mb-5 flex items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold tracking-normal text-ink">Debt payoff</h2>
                <p className="text-sm text-slate-500">Credit cards and loans, excluding mortgage balance</p>
              </div>
              <CircleAlert className="text-amber" size={22} aria-hidden="true" />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-md border border-slate-200 p-4">
                <p className="text-sm text-slate-500">Consumer debt</p>
                <p className="mt-2 text-2xl font-semibold text-ink">{formatGBP(consumerDebt)}</p>
              </div>
              <div className="rounded-md border border-slate-200 p-4">
                <p className="text-sm text-slate-500">Monthly payment</p>
                <p className="mt-2 text-2xl font-semibold text-ink">{formatGBP(activeProfile.monthlyDebtPayment)}</p>
              </div>
              <div className="rounded-md border border-slate-200 p-4">
                <p className="text-sm text-slate-500">Payoff time</p>
                <p className="mt-2 text-2xl font-semibold text-ink">{formatMonths(payoff.months)}</p>
              </div>
              <div className="rounded-md border border-slate-200 p-4">
                <p className="text-sm text-slate-500">Estimated interest</p>
                <p className="mt-2 text-2xl font-semibold text-ink">
                  {payoff.interest === null ? "n/a" : formatGBP(payoff.interest)}
                </p>
              </div>
            </div>
            <div className="mt-5 rounded-md border border-slate-200 p-4 text-sm text-slate-600">
              {payoff.months === null ? (
                <p>The current payment is below the estimated monthly interest of {formatGBP(interestOnlyPayment)}.</p>
              ) : (
                <p>
                  At {formatPercent(activeProfile.averageDebtApr, 1)} APR, this payment clears the consumer debt in{" "}
                  {formatMonths(payoff.months)}.
                </p>
              )}
            </div>
          </section>

          <section className="rounded-md border border-slate-200 bg-panel p-5 shadow-soft">
            <div className="mb-5 flex items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold tracking-normal text-ink">Debt mix</h2>
                <p className="text-sm text-slate-500">Balances from setup</p>
              </div>
              <ReceiptText className="text-cobalt" size={22} aria-hidden="true" />
            </div>
            <div className="grid gap-3 text-sm">
              <div className="flex items-center justify-between rounded-md border border-slate-200 p-3">
                <span className="text-slate-600">Credit cards</span>
                <span className="font-semibold text-ink">{formatGBP(activeProfile.creditCardBalance)}</span>
              </div>
              <div className="flex items-center justify-between rounded-md border border-slate-200 p-3">
                <span className="text-slate-600">Loans and overdraft</span>
                <span className="font-semibold text-ink">{formatGBP(activeProfile.loanBalance)}</span>
              </div>
              <div className="flex items-center justify-between rounded-md border border-slate-200 p-3">
                <span className="text-slate-600">Mortgage</span>
                <span className="font-semibold text-ink">{formatGBP(activeProfile.mortgageBalance)}</span>
              </div>
              <div className="flex items-center justify-between rounded-md border border-slate-200 p-3">
                <span className="text-slate-600">Payment-to-income</span>
                <span className="font-semibold text-ink">{formatPercent(monthlyDebtToIncome, 1)}</span>
              </div>
            </div>
          </section>
        </div>
      ) : null}

      {activeView === "goals" ? (
        <div className="mx-auto grid max-w-7xl gap-5 px-5 py-6 lg:grid-cols-[1fr_1fr]">
          <section className="rounded-md border border-slate-200 bg-panel p-5 shadow-soft">
            <div className="mb-5 flex items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold tracking-normal text-ink">Emergency fund</h2>
                <p className="text-sm text-slate-500">Cash savings against your emergency target</p>
              </div>
              <PiggyBank className="text-teal" size={22} aria-hidden="true" />
            </div>
            <div className="flex items-end justify-between gap-4">
              <div>
                <p className="text-sm text-slate-500">Current cash</p>
                <p className="mt-2 text-3xl font-semibold text-ink">{formatGBP(activeProfile.liquidSavings)}</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-slate-500">Target</p>
                <p className="mt-2 text-xl font-semibold text-ink">{formatGBP(activeProfile.emergencyFundTarget)}</p>
              </div>
            </div>
            <div className="mt-5 h-3 rounded-sm bg-slate-100">
              <div className="h-3 rounded-sm bg-teal" style={{ width: `${emergencyProgress}%` }} />
            </div>
            <div className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
              <div className="rounded-md border border-slate-200 p-3">
                <p className="text-slate-500">Gap</p>
                <p className="mt-1 font-semibold text-ink">{formatGBP(emergencyGap)}</p>
              </div>
              <div className="rounded-md border border-slate-200 p-3">
                <p className="text-slate-500">Time at current contribution</p>
                <p className="mt-1 font-semibold text-ink">{formatMonths(monthsToEmergency)}</p>
              </div>
            </div>
          </section>

          <section className="rounded-md border border-slate-200 bg-panel p-5 shadow-soft">
            <div className="mb-5 flex items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold tracking-normal text-ink">Savings goal</h2>
                <p className="text-sm text-slate-500">Progress after protecting the emergency fund</p>
              </div>
              <CheckCircle2 className="text-cobalt" size={22} aria-hidden="true" />
            </div>
            <div className="flex items-end justify-between gap-4">
              <div>
                <p className="text-sm text-slate-500">Available for goal</p>
                <p className="mt-2 text-3xl font-semibold text-ink">{formatGBP(goalStartingBalance)}</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-slate-500">Target</p>
                <p className="mt-2 text-xl font-semibold text-ink">{formatGBP(activeProfile.savingsGoalTarget)}</p>
              </div>
            </div>
            <div className="mt-5 h-3 rounded-sm bg-slate-100">
              <div className="h-3 rounded-sm bg-cobalt" style={{ width: `${goalProgress}%` }} />
            </div>
            <div className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
              <div className="rounded-md border border-slate-200 p-3">
                <p className="text-slate-500">Gap</p>
                <p className="mt-1 font-semibold text-ink">{formatGBP(goalGap)}</p>
              </div>
              <div className="rounded-md border border-slate-200 p-3">
                <p className="text-slate-500">Time at current contribution</p>
                <p className="mt-1 font-semibold text-ink">{formatMonths(monthsToGoal)}</p>
              </div>
            </div>
            <p className="mt-4 text-sm text-slate-600">Monthly contribution: {formatGBP(monthlyGoalContribution)}.</p>
          </section>
        </div>
      ) : null}
    </main>
  );
}
