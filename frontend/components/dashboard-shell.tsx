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
  MessageSquareText,
  Pencil,
  PiggyBank,
  Plus,
  ReceiptText,
  RotateCcw,
  Settings,
  SlidersHorizontal,
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
  AdvisorAskResponse,
  CategorySpend,
  DerivedHealthScoreResponse,
  ForecastResponse,
  InflationImpact,
  Metric,
  OnboardingProfile,
  PersonalInflationResponse,
  RateImpactResponse,
  Recommendation,
  TransactionPayload
} from "@/types/finscope";
import { askAdvisor, calculateRateImpact, uploadTransactions } from "@/lib/api";
import { AdvisorPanel } from "@/components/advisor-panel";
import { OnboardingFlow } from "@/components/onboarding-flow";
import {
  emptyProfile,
  normaliseProfile,
  ProfileForm,
  profileHasValues,
  type ProfileSectionId
} from "@/components/profile-form";
import { TransactionEntryModal, type TransactionDraftPreset } from "@/components/transaction-entry-modal";

const fallbackRateImpact: RateImpactResponse = {
  current_bank_rate_pct: 0,
  scenario_bank_rate_pct: 0,
  bank_rate_change_pct_points: 0,
  effective_rate_change_pct_points: 0,
  monthly_net_cashflow_delta: 0,
  annual_net_cashflow_delta: 0,
  lines: [],
  notes: []
};

const categoryPrompts: Record<
  string,
  {
    amount: string;
    description: string;
    intro: string;
    title: string;
  }
> = {
  groceries: {
    amount: "45.00",
    description: "Tesco Superstore",
    intro: "Add a grocery row so food spending, inflation, and simulator estimates have real input.",
    title: "Add grocery spending"
  },
  transport: {
    amount: "25.00",
    description: "TfL Travel Charge",
    intro: "Add a transport row so travel costs can appear in spending, inflation, and forecast views.",
    title: "Add transport spending"
  },
  utilities: {
    amount: "90.00",
    description: "Octopus Energy",
    intro: "Add a utility or bills row so household bills are included in pressure and simulator views.",
    title: "Add bills spending"
  },
  housing: {
    amount: "1000.00",
    description: "Rent Payment",
    intro: "Add a housing row so rent or mortgage spending is represented in the analysis.",
    title: "Add housing spending"
  },
  subscriptions: {
    amount: "10.99",
    description: "Netflix",
    intro: "Add a subscription row so recurring costs can be included in the recommendations.",
    title: "Add subscription spending"
  },
  eating_out: {
    amount: "18.00",
    description: "Pret A Manger",
    intro: "Add an eating-out row so discretionary spending is included in the analysis.",
    title: "Add eating-out spending"
  }
};

type DashboardView =
  | "overview"
  | "spending"
  | "costs"
  | "net-worth"
  | "debt"
  | "goals"
  | "simulator"
  | "actions"
  | "advisor"
  | "profile";

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
  { id: "simulator", label: "Simulator", helper: "What-if changes", icon: SlidersHorizontal },
  { id: "actions", label: "Next actions", helper: "Recommendations and scenario", icon: CheckCircle2 },
  { id: "advisor", label: "Advisor", helper: "Grounded answers", icon: MessageSquareText },
  { id: "profile", label: "Profile", helper: "Setup and targets", icon: Settings }
];

const profileStorageKey = "finscope:financial-profile:v1";

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

function readStoredProfile() {
  if (typeof window === "undefined") return null;

  try {
    const stored = window.localStorage.getItem(profileStorageKey);
    if (!stored) return null;
    return normaliseProfile(JSON.parse(stored) as Partial<Record<keyof OnboardingProfile, unknown>>);
  } catch {
    window.localStorage.removeItem(profileStorageKey);
    return null;
  }
}

function writeStoredProfile(profile: OnboardingProfile) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(profileStorageKey, JSON.stringify(profile));
}

function clearStoredProfile() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(profileStorageKey);
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

function emptyHealthScore(profile?: OnboardingProfile | null): DerivedHealthScoreResponse {
  const income = profile?.monthlyIncome ?? 0;
  return {
    score: 0,
    band: "Needs transactions",
    components: [],
    monthly_income: income,
    monthly_spend: 0,
    savings_rate: 0,
    rent_to_income: income > 0 && profile ? profile.rentOrMortgage / income : 0,
    emergency_fund_months: 0,
    spending_volatility: 0,
    benchmarks: [],
    notes: []
  };
}

function emptyCostOfLiving() {
  return {
    period: "No transaction data",
    personalRate: 0,
    nationalRate: 0,
    chart: [] as InflationImpact[]
  };
}

function csvEscape(value: string | number | null | undefined) {
  const text = value === null || value === undefined ? "" : String(value);
  if (/[",\n]/.test(text)) return `"${text.replaceAll('"', '""')}"`;
  return text;
}

function transactionRowsToCsv(rows: TransactionPayload[]) {
  const columns: Array<keyof TransactionPayload> = [
    "date",
    "description",
    "amount",
    "category",
    "transaction_type",
    "account"
  ];
  return [
    columns.join(","),
    ...rows.map((row) => columns.map((column) => csvEscape(row[column])).join(","))
  ].join("\n");
}

function transactionRowsToFile(rows: TransactionPayload[]) {
  return new File([transactionRowsToCsv(rows)], "form_transactions.csv", { type: "text/csv" });
}

function priorityTone(priority: string) {
  if (priority === "high") return "text-rose";
  if (priority === "medium") return "text-amber";
  return "text-teal";
}

function advisorProfileFromProfile(profile: OnboardingProfile) {
  return {
    monthly_income: profile.monthlyIncome,
    rent_or_mortgage: profile.rentOrMortgage,
    monthly_debt_payment: profile.monthlyDebtPayment,
    liquid_savings: profile.liquidSavings,
    investment_balance: profile.investmentBalance,
    pension_balance: profile.pensionBalance,
    property_value: profile.propertyValue,
    mortgage_balance: profile.mortgageBalance,
    credit_card_balance: profile.creditCardBalance,
    loan_balance: profile.loanBalance,
    average_debt_apr: profile.averageDebtApr,
    emergency_fund_target: profile.emergencyFundTarget,
    savings_goal_target: profile.savingsGoalTarget,
    monthly_goal_contribution: profile.monthlyGoalContribution
  };
}

export function DashboardShell() {
  const [activeProfile, setActiveProfile] = useState<OnboardingProfile | null>(null);
  const [profileDraft, setProfileDraft] = useState<OnboardingProfile>(emptyProfile);
  const [profileSectionFocus, setProfileSectionFocus] = useState<ProfileSectionId | null>(null);
  const [hasCheckedStoredProfile, setHasCheckedStoredProfile] = useState(false);
  const [displayName, setDisplayName] = useState("");
  const [activeView, setActiveView] = useState<DashboardView>("overview");
  const [dataMode, setDataMode] = useState<"empty" | "uploaded" | "manual">("empty");
  const [scenario, setScenario] = useState({
    rentChangePct: 8,
    foodChangePct: 10,
    billsChangePct: 6,
    extraDebtPayment: 50,
    extraSavings: 100
  });
  const [manualRows, setManualRows] = useState<TransactionPayload[]>([]);
  const [transactionRows, setTransactionRows] = useState<TransactionPayload[]>([]);
  const [isTransactionModalOpen, setIsTransactionModalOpen] = useState(false);
  const [transactionPreset, setTransactionPreset] = useState<TransactionDraftPreset | null>(null);
  const [transactionPrompt, setTransactionPrompt] = useState<{
    intro: string;
    title: string;
  } | null>(null);
  const [hasPromptedForSpendingData, setHasPromptedForSpendingData] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<UploadState>({ state: "idle", message: "" });
  const [uploadSummary, setUploadSummary] = useState<UploadSummary | null>(null);
  const [costOfLiving, setCostOfLiving] = useState<{
    period: string;
    personalRate: number;
    nationalRate: number;
    chart: InflationImpact[];
  }>(emptyCostOfLiving());
  const [rateImpact, setRateImpact] = useState<RateImpactResponse>(fallbackRateImpact);
  const [healthScore, setHealthScore] = useState<DerivedHealthScoreResponse>(emptyHealthScore());
  const [forecastRows, setForecastRows] = useState<CategorySpend[]>([]);
  const [forecastPeriod, setForecastPeriod] = useState("No forecast yet");
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [latestForecast, setLatestForecast] = useState<ForecastResponse | null>(null);
  const [personalInflation, setPersonalInflation] = useState<PersonalInflationResponse | null>(null);
  const [advisorAnswer, setAdvisorAnswer] = useState<AdvisorAskResponse | null>(null);
  const [advisorStatus, setAdvisorStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [advisorError, setAdvisorError] = useState("");

  useEffect(() => {
    const storedProfile = readStoredProfile();
    if (storedProfile) {
      setActiveProfile(storedProfile);
      setProfileDraft(storedProfile);
      setHealthScore(emptyHealthScore(storedProfile));
    }
    setHasCheckedStoredProfile(true);
  }, []);

  useEffect(() => {
    if (!activeProfile) return;
    let isMounted = true;

    async function loadRateImpact() {
      if (!activeProfile) return;

      const variableDebtBalance = activeProfile.creditCardBalance + activeProfile.loanBalance;
      try {
        const rateResponse = await calculateRateImpact({
          savings_balance: activeProfile.liquidSavings,
          variable_debt_balance: variableDebtBalance,
          mortgage_balance: activeProfile.mortgageBalance > 0 ? activeProfile.mortgageBalance : undefined,
          mortgage_years_remaining: 22,
          current_mortgage_rate_pct: 5,
          bank_rate_change_pct_points: 0.25
        });
        if (!isMounted) return;
        setRateImpact(rateResponse);
      } catch {
        if (!isMounted) return;
      }
    }

    if (dataMode === "empty") {
      setHealthScore(emptyHealthScore(activeProfile));
    }
    void loadRateImpact();

    return () => {
      isMounted = false;
    };
  }, [activeProfile, dataMode]);

  useEffect(() => {
    if (!activeProfile || activeView !== "spending" || dataMode !== "empty" || hasPromptedForSpendingData) return;
    setIsTransactionModalOpen(true);
    setHasPromptedForSpendingData(true);
  }, [activeProfile, activeView, dataMode, hasPromptedForSpendingData]);

  async function analyseTransactionFile(
    file: File,
    source: "uploaded" | "manual",
    profileOverride?: OnboardingProfile,
    nextView: DashboardView = "overview"
  ) {
    const profileForAnalysis = profileOverride ?? activeProfile ?? undefined;
    const sourceLabel = source === "uploaded" ? "CSV" : "form rows";
    setUploadStatus({ state: "loading", message: `Analysing ${sourceLabel}` });
    setUploadSummary(null);
    try {
      const result = await uploadTransactions(file, profileForAnalysis);
      setUploadStatus({
        state: "success",
        message: `${result.rows} rows, GBP ${Number(result.total_spend).toLocaleString()} spend`
      });
      setUploadSummary(uploadSummaryFromResult(result));
      setDataMode(source);
      setActiveView(nextView);
      setLatestForecast(result.forecast);
      setPersonalInflation(result.personal_inflation);
      setAdvisorAnswer(null);
      setAdvisorStatus("idle");
      setAdvisorError("");
      setTransactionRows(
        result.transactions.map((transaction) => ({
          date: transaction.date,
          description: transaction.description,
          amount: transaction.amount,
          category: transaction.category ?? transaction.predicted_category,
          transaction_type: transaction.transaction_type,
          account: transaction.account
        }))
      );

      setForecastPeriod(result.forecast.period);
      setForecastRows(
        result.forecast.forecasts.length > 0 ? forecastRowsFromResponse(result.forecast, result.transactions) : []
      );

      setCostOfLiving(
        result.personal_inflation
          ? {
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
            }
          : emptyCostOfLiving()
      );

      setHealthScore(result.health_score ?? emptyHealthScore(profileForAnalysis));
      setRecommendations(result.recommendations);
    } catch (error) {
      setUploadSummary(null);
      setUploadStatus({
        state: "error",
        message: error instanceof Error ? error.message : "Transaction analysis failed"
      });
    }
  }

  async function handleUpload(file: File | undefined) {
    if (!file) return;
    await analyseTransactionFile(file, "uploaded");
  }

  async function handleManualAnalyse(rows: TransactionPayload[]) {
    setManualRows(rows);
    await analyseTransactionFile(transactionRowsToFile(rows), "manual");
    setIsTransactionModalOpen(false);
    setTransactionPreset(null);
    setTransactionPrompt(null);
  }

  async function handleProfileSave(profile: OnboardingProfile) {
    writeStoredProfile(profile);
    setActiveProfile(profile);
    setProfileDraft(profile);
    setProfileSectionFocus(null);
    setAdvisorAnswer(null);
    setAdvisorStatus("idle");
    setAdvisorError("");

    if (dataMode === "empty" || transactionRows.length === 0) {
      setHealthScore(emptyHealthScore(profile));
      return;
    }

    await analyseTransactionFile(transactionRowsToFile(transactionRows), dataMode, profile, activeView);
  }

  function openProfileEditor(section?: ProfileSectionId) {
    if (!activeProfile) return;
    setProfileDraft(activeProfile);
    setProfileSectionFocus(section ?? null);
    setActiveView("profile");
  }

  function resetProfileAndData() {
    clearStoredProfile();
    setActiveProfile(null);
    setProfileDraft(emptyProfile);
    setProfileSectionFocus(null);
    setActiveView("overview");
    setDataMode("empty");
    setManualRows([]);
    setUploadSummary(null);
    setTransactionRows([]);
    setForecastRows([]);
    setForecastPeriod("No forecast yet");
    setLatestForecast(null);
    setPersonalInflation(null);
    setCostOfLiving(emptyCostOfLiving());
    setHealthScore(emptyHealthScore());
    setRecommendations([]);
    setAdvisorAnswer(null);
    setAdvisorStatus("idle");
    setAdvisorError("");
    setUploadStatus({ state: "idle", message: "" });
  }

  const isAnalysingTransactions = uploadStatus.state === "loading";
  const mortgageImpact = rateImpact.lines.find((line) => line.name === "Repayment mortgage");
  const savingsImpact = rateImpact.lines.find((line) => line.name === "Savings interest");
  const debtImpact = rateImpact.lines.find((line) => line.name === "Variable debt cost");
  const hasFinancialSetup = activeProfile ? profileHasValues(activeProfile) : false;
  const needsIncome = (activeProfile?.monthlyIncome ?? 0) <= 0;
  const income = activeProfile?.monthlyIncome ?? healthScore.monthly_income;
  const spend = healthScore.monthly_spend;
  const disposable = income - spend;
  const dashboardMetrics: Metric[] = [
    {
      label: "Monthly income",
      value: income > 0 ? `GBP ${Math.round(income).toLocaleString()}` : "Not set",
      delta: income > 0 ? "From setup" : "Add it in Profile",
      tone: income > 0 ? "neutral" : "watch"
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
  const dataModeLabel =
    dataMode === "uploaded" ? "Uploaded CSV" : dataMode === "manual" ? "Form entries" : "No transactions";
  const dataModeDetail =
    !hasFinancialSetup
      ? "Start with your own setup values, then add transactions to unlock spend, forecast, inflation, and action insights."
      : dataMode === "uploaded"
      ? "Spend, forecast, inflation, health score, and actions are using the latest CSV analysis."
      : dataMode === "manual"
        ? "Spend, forecast, inflation, health score, and actions are using the transaction rows entered in the form."
        : "Add transactions with the form or upload a CSV to unlock spending, forecast, inflation, and action insights.";
  const totalAssets =
    (activeProfile?.liquidSavings ?? 0) +
    (activeProfile?.investmentBalance ?? 0) +
    (activeProfile?.pensionBalance ?? 0) +
    (activeProfile?.propertyValue ?? 0);
  const consumerDebt = (activeProfile?.creditCardBalance ?? 0) + (activeProfile?.loanBalance ?? 0);
  const totalLiabilities = (activeProfile?.mortgageBalance ?? 0) + consumerDebt;
  const netWorth = totalAssets - totalLiabilities;
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
  const spendToIncome = (spend / Math.max(income, 1)) * 100;
  const forecastSpendTotal = forecastRows.reduce((total, row) => total + row.forecast, 0);
  const forecastToIncome = (forecastSpendTotal / Math.max(income, 1)) * 100;
  const personalInflationGap = costOfLiving.personalRate - costOfLiving.nationalRate;
  const groceriesForecast = forecastRows.find((row) => row.category.toLowerCase().includes("grocer"))?.forecast ?? 0;
  const utilitiesForecast =
    forecastRows.find((row) => row.category.toLowerCase().includes("util"))?.forecast ??
    forecastRows.find((row) => row.category.toLowerCase().includes("bill"))?.forecast ??
    0;
  const housingBase = activeProfile?.rentOrMortgage ?? 0;
  const rentScenarioDelta = housingBase * (scenario.rentChangePct / 100);
  const foodScenarioDelta = groceriesForecast * (scenario.foodChangePct / 100);
  const billsScenarioDelta = utilitiesForecast * (scenario.billsChangePct / 100);
  const scenarioPressure =
    rentScenarioDelta +
    foodScenarioDelta +
    billsScenarioDelta +
    scenario.extraDebtPayment +
    scenario.extraSavings;
  const scenarioCashLeft = disposable - scenarioPressure;
  const scenarioMonthlyGoalContribution = Math.max(monthlyGoalContribution + scenario.extraSavings, 0);
  const scenarioMonthsToEmergency =
    emergencyGap <= 0
      ? 0
      : scenarioMonthlyGoalContribution > 0
        ? Math.ceil(emergencyGap / scenarioMonthlyGoalContribution)
        : null;
  const pressurePoints = [
    {
      label: "Spend-to-income",
      value: formatPercent(spendToIncome, 0),
      detail: `${formatGBP(spend)} monthly spend`,
      tone: spendToIncome < 75 ? "good" : spendToIncome < 90 ? "watch" : "risk",
      bar: spendToIncome
    },
    {
      label: "Housing burden",
      value: formatPercent(healthScore.rent_to_income * 100, 0),
      detail: `${formatGBP(activeProfile?.rentOrMortgage ?? 0)} rent or mortgage`,
      tone: healthScore.rent_to_income < 0.3 ? "good" : healthScore.rent_to_income < 0.4 ? "watch" : "risk",
      bar: healthScore.rent_to_income * 100
    },
    {
      label: "Emergency cover",
      value: `${healthScore.emergency_fund_months.toFixed(1)} months`,
      detail: `${formatGBP(activeProfile?.liquidSavings ?? 0)} liquid savings`,
      tone: healthScore.emergency_fund_months >= 3 ? "good" : healthScore.emergency_fund_months >= 1 ? "watch" : "risk",
      bar: progressPercentage(healthScore.emergency_fund_months, 6)
    },
    {
      label: "Debt payment load",
      value: formatPercent(monthlyDebtToIncome, 1),
      detail: `${formatGBP(activeProfile?.monthlyDebtPayment ?? 0)} paid each month`,
      tone: monthlyDebtToIncome < 10 ? "good" : monthlyDebtToIncome < 20 ? "watch" : "risk",
      bar: monthlyDebtToIncome
    },
    {
      label: "Next forecast pressure",
      value: formatPercent(forecastToIncome, 0),
      detail: `${formatGBP(forecastSpendTotal)} forecast spend`,
      tone: forecastToIncome < 75 ? "good" : forecastToIncome < 90 ? "watch" : "risk",
      bar: forecastToIncome
    },
    {
      label: "Personal inflation gap",
      value: `${personalInflationGap >= 0 ? "+" : ""}${personalInflationGap.toFixed(1)} pp`,
      detail: `${costOfLiving.personalRate.toFixed(1)}% personal vs ${costOfLiving.nationalRate.toFixed(1)}% UK`,
      tone: personalInflationGap <= 0 ? "good" : personalInflationGap <= 1 ? "watch" : "risk",
      bar: Math.abs(personalInflationGap) * 25
    }
  ] satisfies Array<{
    label: string;
    value: string;
    detail: string;
    tone: Metric["tone"];
    bar: number;
  }>;
  const scenarioRows = [
    {
      label: "Rent or mortgage",
      base: housingBase,
      assumption: `${scenario.rentChangePct >= 0 ? "+" : ""}${scenario.rentChangePct}%`,
      delta: rentScenarioDelta
    },
    {
      label: "Food and groceries",
      base: groceriesForecast,
      assumption: `${scenario.foodChangePct >= 0 ? "+" : ""}${scenario.foodChangePct}%`,
      delta: foodScenarioDelta
    },
    {
      label: "Bills and utilities",
      base: utilitiesForecast,
      assumption: `${scenario.billsChangePct >= 0 ? "+" : ""}${scenario.billsChangePct}%`,
      delta: billsScenarioDelta
    },
    {
      label: "Extra debt payment",
      base: activeProfile?.monthlyDebtPayment ?? 0,
      assumption: formatGBP(scenario.extraDebtPayment),
      delta: scenario.extraDebtPayment
    },
    {
      label: "Extra savings",
      base: monthlyGoalContribution,
      assumption: formatGBP(scenario.extraSavings),
      delta: scenario.extraSavings
    }
  ];
  const scenarioControls = [
    {
      label: "Rent or mortgage change",
      field: "rentChangePct",
      value: scenario.rentChangePct,
      min: -20,
      max: 30,
      step: 1,
      suffix: "%",
      detail: `${formatGBP(housingBase)} current housing cost`
    },
    {
      label: "Food price change",
      field: "foodChangePct",
      value: scenario.foodChangePct,
      min: -20,
      max: 30,
      step: 1,
      suffix: "%",
      detail: `${formatGBP(groceriesForecast)} forecast groceries`
    },
    {
      label: "Bills price change",
      field: "billsChangePct",
      value: scenario.billsChangePct,
      min: -20,
      max: 30,
      step: 1,
      suffix: "%",
      detail: `${formatGBP(utilitiesForecast)} forecast utilities`
    },
    {
      label: "Extra debt payment",
      field: "extraDebtPayment",
      value: scenario.extraDebtPayment,
      min: 0,
      max: 500,
      step: 10,
      suffix: "GBP",
      detail: "Additional monthly debt overpayment"
    },
    {
      label: "Extra savings",
      field: "extraSavings",
      value: scenario.extraSavings,
      min: 0,
      max: 500,
      step: 10,
      suffix: "GBP",
      detail: "Additional monthly savings contribution"
    }
  ] satisfies Array<{
    label: string;
    field: keyof typeof scenario;
    value: number;
    min: number;
    max: number;
    step: number;
    suffix: "%" | "GBP";
    detail: string;
  }>;
  const netWorthRows = [
    { label: "Cash savings", value: activeProfile?.liquidSavings ?? 0, tone: "text-teal" },
    { label: "Investments", value: activeProfile?.investmentBalance ?? 0, tone: "text-cobalt" },
    { label: "Pension", value: activeProfile?.pensionBalance ?? 0, tone: "text-amber" },
    { label: "Property", value: activeProfile?.propertyValue ?? 0, tone: "text-slate-600" },
    { label: "Mortgage", value: -(activeProfile?.mortgageBalance ?? 0), tone: "text-rose" },
    { label: "Cards and loans", value: -consumerDebt, tone: "text-rose" }
  ];

  function updateScenario(key: keyof typeof scenario, value: number) {
    setScenario((current) => ({
      ...current,
      [key]: value
    }));
  }

  function hasCategory(category: string) {
    return transactionRows.some((transaction) => transaction.category === category);
  }

  function openTransactionPrompt(category: string) {
    const prompt = categoryPrompts[category] ?? {
      amount: "25.00",
      description: displayCategory(category),
      intro: `Add a ${displayCategory(category).toLowerCase()} row so this section can use it in the analysis.`,
      title: `Add ${displayCategory(category).toLowerCase()} spending`
    };

    setTransactionPreset({
      amount: prompt.amount,
      category,
      description: prompt.description,
      transaction_type: category === "income" ? "income" : "expense",
      account: "current"
    });
    setTransactionPrompt({
      intro: prompt.intro,
      title: prompt.title
    });
    setIsTransactionModalOpen(true);
  }

  async function handleAskAdvisor(question: string) {
    if (!activeProfile) {
      setAdvisorStatus("error");
      setAdvisorError("Add your profile setup before asking the advisor.");
      return;
    }

    const advisorProfile = advisorProfileFromProfile(activeProfile);
    setAdvisorStatus("loading");
    setAdvisorError("");

    try {
      const response = await askAdvisor({
        question,
        max_chunks: 4,
        profile: advisorProfile,
        transactions: transactionRows,
        forecast: latestForecast,
        personal_inflation: personalInflation,
        health_score: dataMode === "empty" ? null : healthScore,
        rate_impact: rateImpact.lines.length > 0 ? rateImpact : null,
        recommendations
      });

      setAdvisorAnswer(response);
      setAdvisorStatus("success");
    } catch (error) {
      setAdvisorStatus("error");
      setAdvisorError(error instanceof Error ? error.message : "Advisor answer failed");
    }
  }

  function handleResolveAdvisorMissing(item: AdvisorAskResponse["missing_data"][number]) {
    if (item.key === "profile") {
      openProfileEditor();
      return;
    }

    if (item.key === "monthly_income") {
      openProfileEditor("cash-flow");
      return;
    }

    if (item.key === "transactions" || item.key === "forecast" || item.key === "personal_inflation" || item.key === "health_score") {
      setTransactionPreset(null);
      setTransactionPrompt(null);
      setIsTransactionModalOpen(true);
      return;
    }

    if (item.key === "rate_impact") {
      openProfileEditor("debts");
      return;
    }

    if (item.key.startsWith("category_")) {
      openTransactionPrompt(item.key.replace("category_", ""));
    }
  }

  const missingCostOfLivingCategories = ["groceries", "transport", "utilities", "housing"].filter(
    (category) => !hasCategory(category)
  );
  const missingSpendingCategories = ["groceries", "transport", "utilities", "subscriptions", "eating_out"].filter(
    (category) => !hasCategory(category)
  );
  const missingSimulatorCategories = ["groceries", "utilities", "housing"].filter((category) => !hasCategory(category));
  const missingRecommendationCategories = ["subscriptions", "eating_out", "transport"].filter(
    (category) => !hasCategory(category)
  );

  if (!hasCheckedStoredProfile) {
    return (
      <main className="grid min-h-screen place-items-center bg-paper px-5 py-8">
        <div className="flex items-center gap-3 rounded-md border border-slate-200 bg-panel px-4 py-3 text-sm font-semibold text-slate-600 shadow-soft">
          <LoaderCircle className="animate-spin text-cobalt" size={18} aria-hidden="true" />
          Loading your setup
        </div>
      </main>
    );
  }

  if (!activeProfile) {
    return (
      <OnboardingFlow
        onReady={(profile, name) => {
          setDisplayName(name);
          writeStoredProfile(profile);
          setProfileDraft(profile);
          setDataMode("empty");
          setUploadSummary(null);
          setForecastRows([]);
          setTransactionRows([]);
          setForecastPeriod("No forecast yet");
          setLatestForecast(null);
          setPersonalInflation(null);
          setCostOfLiving(emptyCostOfLiving());
          setHealthScore(emptyHealthScore(profile));
          setRecommendations([]);
          setAdvisorAnswer(null);
          setAdvisorStatus("idle");
          setAdvisorError("");
          setActiveProfile(profile);
        }}
      />
    );
  }

  return (
    <main className="min-h-screen bg-paper">
      <header className="border-b border-slate-200 bg-panel">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-5 py-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-normal text-cobalt">FinScope UK</p>
            <h1 className="mt-1 text-2xl font-semibold tracking-normal text-ink sm:text-3xl">
              {displayName ? `Hello, ${displayName}` : "Personal finance dashboard"}
            </h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">{dataModeDetail}</p>
          </div>
          <div className="flex flex-col items-start gap-2 sm:items-end">
            <div className="flex flex-wrap justify-end gap-2">
              <button
                className="focus-ring inline-flex h-11 items-center justify-center gap-2 rounded-md bg-ink px-4 text-sm font-semibold text-white shadow-soft transition hover:bg-slate-800"
                type="button"
                onClick={() => {
                  setTransactionPreset(null);
                  setTransactionPrompt(null);
                  setIsTransactionModalOpen(true);
                }}
              >
                <Plus size={18} aria-hidden="true" />
                Add transaction
              </button>
              <label className="focus-ring inline-flex h-11 cursor-pointer items-center justify-center gap-2 rounded-md border border-slate-200 px-4 text-sm font-semibold text-slate-600 transition hover:border-cobalt">
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
                onClick={() => openProfileEditor()}
              >
                <Settings size={18} aria-hidden="true" />
                Profile setup
              </button>
            </div>
            <p className="flex flex-wrap items-center justify-end gap-2 text-sm font-medium text-slate-500">
              <span
                className={`rounded-sm px-2 py-1 text-xs font-semibold uppercase ${
                  dataMode === "uploaded"
                    ? "bg-emerald-50 text-teal"
                    : dataMode === "manual"
                      ? "bg-amber/10 text-amber"
                      : "bg-blue-50 text-cobalt"
                }`}
              >
                {dataModeLabel}
              </span>
              <span>{activeProfile.monthlyIncome > 0 ? `Income ${formatGBP(activeProfile.monthlyIncome)}` : "Income not set"}</span>
            </p>
          </div>
        </div>
      </header>

      <TransactionEntryModal
        initialDraft={transactionPreset}
        intro={transactionPrompt?.intro}
        isAnalysing={isAnalysingTransactions}
        open={isTransactionModalOpen}
        rows={manualRows}
        title={transactionPrompt?.title}
        onAnalyse={handleManualAnalyse}
        onClose={() => {
          setIsTransactionModalOpen(false);
          setTransactionPreset(null);
          setTransactionPrompt(null);
        }}
        onRowsChange={setManualRows}
      />

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
              {!hasFinancialSetup || needsIncome ? (
                <section className="rounded-md border border-dashed border-slate-300 bg-panel p-5 shadow-soft">
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <h2 className="text-lg font-semibold tracking-normal text-ink">Finish financial setup</h2>
                      <p className="mt-1 text-sm leading-6 text-slate-500">
                        Add your own income, balances, debts, and targets so these numbers are based on you.
                      </p>
                    </div>
                    <button
                      className="focus-ring inline-flex h-11 items-center justify-center gap-2 rounded-md bg-ink px-4 text-sm font-semibold text-white"
                      type="button"
                      onClick={() => openProfileEditor(needsIncome ? "cash-flow" : undefined)}
                    >
                      <Settings size={18} aria-hidden="true" />
                      Open setup
                    </button>
                  </div>
                </section>
              ) : null}

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
                    <h2 className="text-lg font-semibold tracking-normal text-ink">Pressure points</h2>
                    <p className="text-sm text-slate-500">The main signals that can squeeze monthly cash flow</p>
                  </div>
                  <Home className="text-cobalt" size={22} aria-hidden="true" />
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  {pressurePoints.map((point) => (
                    <div key={point.label} className="rounded-md border border-slate-200 p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold text-ink">{point.label}</p>
                          <p className="mt-1 text-xs leading-5 text-slate-500">{point.detail}</p>
                        </div>
                        <span className={`text-sm font-semibold ${toneClass(point.tone)}`}>{point.value}</span>
                      </div>
                      <div className="mt-4 h-2 rounded-sm bg-slate-100">
                        <div
                          className={`h-2 rounded-sm ${
                            point.tone === "good" ? "bg-teal" : point.tone === "watch" ? "bg-amber" : "bg-rose"
                          }`}
                          style={{ width: `${clampPercentage(point.bar)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            </>
          ) : null}

          {activeView === "spending" && forecastRows.length > 0 ? (
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

          {activeView === "spending" && forecastRows.length === 0 ? (
            <section className="rounded-md border border-dashed border-slate-300 bg-panel p-6 shadow-soft">
              <div className="mx-auto grid max-w-2xl gap-4 text-center">
                <ReceiptText className="mx-auto text-cobalt" size={30} aria-hidden="true" />
                <div>
                  <h2 className="text-xl font-semibold tracking-normal text-ink">Add spending rows</h2>
                  <p className="mt-2 text-sm leading-6 text-slate-500">
                    Spending, forecasts, inflation, and recommendations stay empty until transactions are added.
                  </p>
                </div>
                <div className="flex flex-col justify-center gap-3 sm:flex-row">
                  <button
                    className="focus-ring inline-flex h-11 items-center justify-center gap-2 rounded-md bg-ink px-4 text-sm font-semibold text-white"
                    type="button"
                    onClick={() => {
                      setTransactionPreset(null);
                      setTransactionPrompt(null);
                      setIsTransactionModalOpen(true);
                    }}
                  >
                    <Plus size={18} aria-hidden="true" />
                    Enter transactions
                  </button>
                  <label className="focus-ring inline-flex h-11 cursor-pointer items-center justify-center gap-2 rounded-md border border-slate-200 px-4 text-sm font-semibold text-slate-600">
                    <Upload size={18} aria-hidden="true" />
                    Upload CSV
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
            </section>
          ) : null}

          {activeView === "spending" && forecastRows.length > 0 ? (
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
              {missingSpendingCategories.length > 0 ? (
                <div className="mt-4 rounded-md border border-dashed border-slate-300 p-4">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="text-sm font-semibold text-ink">Add more spending coverage</p>
                      <p className="mt-1 text-xs leading-5 text-slate-500">
                        These categories are missing from the current transaction set.
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {missingSpendingCategories.slice(0, 4).map((category) => (
                        <button
                          key={category}
                          className="focus-ring inline-flex h-9 items-center justify-center gap-2 rounded-md border border-slate-200 px-3 text-xs font-semibold text-slate-600"
                          type="button"
                          onClick={() => openTransactionPrompt(category)}
                        >
                          <Plus size={15} aria-hidden="true" />
                          {displayCategory(category)}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              ) : null}
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
            {missingCostOfLivingCategories.length > 0 ? (
              <div className="mt-4 rounded-md border border-dashed border-slate-300 p-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm font-semibold text-ink">Missing cost-of-living inputs</p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">
                      Add these rows to improve personal inflation and category pressure.
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {missingCostOfLivingCategories.map((category) => (
                      <button
                        key={category}
                        className="focus-ring inline-flex h-9 items-center justify-center gap-2 rounded-md border border-slate-200 px-3 text-xs font-semibold text-slate-600"
                        type="button"
                        onClick={() => openTransactionPrompt(category)}
                      >
                        <Plus size={15} aria-hidden="true" />
                        {displayCategory(category)}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : null}
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

          {activeView === "costs" ? (
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

          {activeView === "actions" ? (
            <section className="rounded-md border border-slate-200 bg-panel p-5 shadow-soft">
            <div className="mb-4 flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold tracking-normal text-ink">Next actions</h2>
              <PiggyBank className="text-teal" size={22} aria-hidden="true" />
            </div>
            {recommendations.length > 0 ? (
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
            ) : (
              <div className="rounded-md border border-dashed border-slate-300 p-4 text-sm text-slate-500">
                Add transaction rows to generate recommendations.
              </div>
            )}
            {missingRecommendationCategories.length > 0 ? (
              <div className="mt-4 rounded-md border border-dashed border-slate-300 p-4">
                <p className="text-sm font-semibold text-ink">Improve recommendation coverage</p>
                <p className="mt-1 text-xs leading-5 text-slate-500">
                  These rows help the app spot travel, subscription, and discretionary actions.
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {missingRecommendationCategories.map((category) => (
                    <button
                      key={category}
                      className="focus-ring inline-flex h-9 items-center justify-center gap-2 rounded-md border border-slate-200 px-3 text-xs font-semibold text-slate-600"
                      type="button"
                      onClick={() => openTransactionPrompt(category)}
                    >
                      <Plus size={15} aria-hidden="true" />
                      {displayCategory(category)}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}
          </section>
          ) : null}
        </aside>
        </div>
      ) : null}

      {activeView === "advisor" ? (
        <AdvisorPanel
          answer={advisorAnswer}
          errorMessage={advisorError}
          status={advisorStatus}
          onAsk={(question) => {
            void handleAskAdvisor(question);
          }}
          onResolveMissing={handleResolveAdvisorMissing}
        />
      ) : null}

      {activeView === "profile" ? (
        <div className="mx-auto grid max-w-7xl gap-5 px-5 py-6 lg:grid-cols-[0.75fr_1.25fr]">
          <section className="rounded-md border border-slate-200 bg-panel p-5 shadow-soft">
            <div className="mb-5 flex items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold tracking-normal text-ink">Financial setup</h2>
                <p className="text-sm text-slate-500">Saved in this browser and used across the dashboard</p>
              </div>
              <Settings className="text-cobalt" size={22} aria-hidden="true" />
            </div>

            <div className="grid gap-3 text-sm">
              <div className="flex items-center justify-between rounded-md border border-slate-200 p-3">
                <span className="text-slate-600">Setup status</span>
                <span className={`font-semibold ${hasFinancialSetup ? "text-teal" : "text-amber"}`}>
                  {hasFinancialSetup ? "Started" : "Empty"}
                </span>
              </div>
              <div className="flex items-center justify-between rounded-md border border-slate-200 p-3">
                <span className="text-slate-600">Monthly income</span>
                <span className="font-semibold text-ink">
                  {activeProfile.monthlyIncome > 0 ? formatGBP(activeProfile.monthlyIncome) : "Not set"}
                </span>
              </div>
              <div className="flex items-center justify-between rounded-md border border-slate-200 p-3">
                <span className="text-slate-600">Assets</span>
                <span className="font-semibold text-ink">{formatGBP(totalAssets)}</span>
              </div>
              <div className="flex items-center justify-between rounded-md border border-slate-200 p-3">
                <span className="text-slate-600">Liabilities</span>
                <span className="font-semibold text-ink">{formatGBP(totalLiabilities)}</span>
              </div>
              <div className="flex items-center justify-between rounded-md border border-slate-200 p-3">
                <span className="text-slate-600">Goal contribution</span>
                <span className="font-semibold text-ink">{formatGBP(monthlyGoalContribution)}</span>
              </div>
            </div>

            {needsIncome ? (
              <div className="mt-4 rounded-md border border-dashed border-amber/50 bg-amber/5 p-4 text-sm text-slate-600">
                Add monthly income when you can. Without it, spend-to-income and health-score signals stay limited.
              </div>
            ) : null}

            <button
              className="focus-ring mt-5 inline-flex h-11 w-full items-center justify-center gap-2 rounded-md border border-rose/30 px-4 text-sm font-semibold text-rose"
              type="button"
              onClick={resetProfileAndData}
            >
              <RotateCcw size={18} aria-hidden="true" />
              Start setup again
            </button>
          </section>

          <div className="grid gap-4">
            <div className="rounded-md border border-slate-200 bg-panel p-5 shadow-soft">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h2 className="text-lg font-semibold tracking-normal text-ink">Edit setup values</h2>
                  <p className="mt-1 text-sm leading-6 text-slate-500">
                    These values power net worth, debt payoff, savings goals, rate impact, and the health score.
                  </p>
                </div>
                {profileSectionFocus ? (
                  <span className="rounded-sm bg-blue-50 px-2 py-1 text-xs font-semibold uppercase text-cobalt">
                    Editing {profileSectionFocus.replace("-", " ")}
                  </span>
                ) : null}
              </div>
            </div>

            <ProfileForm
              cancelLabel="Undo edits"
              highlightedSection={profileSectionFocus}
              profile={profileDraft}
              saveLabel={dataMode === "empty" ? "Save setup" : "Save and refresh analysis"}
              onCancel={() => {
                setProfileDraft(activeProfile);
                setProfileSectionFocus(null);
              }}
              onProfileChange={setProfileDraft}
              onSave={() => {
                void handleProfileSave(profileDraft);
              }}
            />
          </div>
        </div>
      ) : null}

      {activeView === "net-worth" ? (
        <div className="mx-auto grid max-w-7xl gap-5 px-5 py-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-xl font-semibold tracking-normal text-ink">Net worth</h2>
              <p className="mt-1 text-sm text-slate-500">Assets minus mortgage, cards, loans, and overdraft balances</p>
            </div>
            <button
              className="focus-ring inline-flex h-11 items-center justify-center gap-2 rounded-md border border-slate-200 bg-panel px-4 text-sm font-semibold text-slate-600"
              type="button"
              onClick={() => openProfileEditor("assets")}
            >
              <Pencil size={18} aria-hidden="true" />
              Edit assets
            </button>
          </div>

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
          <div className="flex flex-col gap-3 lg:col-span-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-xl font-semibold tracking-normal text-ink">Debt payoff</h2>
              <p className="mt-1 text-sm text-slate-500">Consumer debt payoff using your balance, payment, and APR</p>
            </div>
            <button
              className="focus-ring inline-flex h-11 items-center justify-center gap-2 rounded-md border border-slate-200 bg-panel px-4 text-sm font-semibold text-slate-600"
              type="button"
              onClick={() => openProfileEditor("debts")}
            >
              <Pencil size={18} aria-hidden="true" />
              Edit debts
            </button>
          </div>

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
          <div className="flex flex-col gap-3 lg:col-span-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-xl font-semibold tracking-normal text-ink">Savings goals</h2>
              <p className="mt-1 text-sm text-slate-500">Emergency cover first, then progress towards the next target</p>
            </div>
            <button
              className="focus-ring inline-flex h-11 items-center justify-center gap-2 rounded-md border border-slate-200 bg-panel px-4 text-sm font-semibold text-slate-600"
              type="button"
              onClick={() => openProfileEditor("goals")}
            >
              <Pencil size={18} aria-hidden="true" />
              Edit goals
            </button>
          </div>

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

      {activeView === "simulator" ? (
        <div className="mx-auto grid max-w-7xl gap-5 px-5 py-6 lg:grid-cols-[1fr_0.9fr]">
          <section className="rounded-md border border-slate-200 bg-panel p-5 shadow-soft">
            <div className="mb-5 flex items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold tracking-normal text-ink">What-if controls</h2>
                <p className="text-sm text-slate-500">Adjust the monthly assumptions and watch the cash impact</p>
              </div>
              <SlidersHorizontal className="text-cobalt" size={22} aria-hidden="true" />
            </div>
            <div className="grid gap-5">
              {scenarioControls.map((control) => (
                <div key={control.field} className="grid gap-3 rounded-md border border-slate-200 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-ink">{control.label}</p>
                      <p className="mt-1 text-xs leading-5 text-slate-500">{control.detail}</p>
                    </div>
                    <span className="text-sm font-semibold text-ink">
                      {control.suffix === "%" ? `${control.value}%` : formatGBP(control.value)}
                    </span>
                  </div>
                  <input
                    className="w-full accent-cobalt"
                    max={control.max}
                    min={control.min}
                    step={control.step}
                    type="range"
                    value={control.value}
                    onChange={(event) => updateScenario(control.field, Number(event.target.value))}
                  />
                  <div className="flex items-center gap-3">
                    <input
                      className="h-10 w-28 rounded-md border border-slate-200 bg-white px-3 text-sm font-semibold text-ink outline-none focus:border-cobalt"
                      max={control.max}
                      min={control.min}
                      step={control.step}
                      type="number"
                      value={control.value}
                      onChange={(event) => updateScenario(control.field, Number(event.target.value))}
                    />
                    <span className="text-xs font-semibold uppercase text-slate-500">
                      {control.suffix === "%" ? "percent" : "per month"}
                    </span>
                  </div>
                </div>
              ))}
              {missingSimulatorCategories.length > 0 ? (
                <div className="rounded-md border border-dashed border-slate-300 p-4">
                  <p className="text-sm font-semibold text-ink">Missing simulator inputs</p>
                  <p className="mt-1 text-xs leading-5 text-slate-500">
                    These rows make the rent, food, and bills scenario more useful.
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {missingSimulatorCategories.map((category) => (
                      <button
                        key={category}
                        className="focus-ring inline-flex h-9 items-center justify-center gap-2 rounded-md border border-slate-200 px-3 text-xs font-semibold text-slate-600"
                        type="button"
                        onClick={() => openTransactionPrompt(category)}
                      >
                        <Plus size={15} aria-hidden="true" />
                        {displayCategory(category)}
                      </button>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          </section>

          <section className="rounded-md border border-slate-200 bg-panel p-5 shadow-soft">
            <div className="mb-5 flex items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold tracking-normal text-ink">Scenario result</h2>
                <p className="text-sm text-slate-500">Monthly position after the selected changes</p>
              </div>
              <Banknote className="text-amber" size={22} aria-hidden="true" />
            </div>
            <div className="grid gap-4">
              <div className="rounded-md border border-slate-200 p-4">
                <p className="text-sm text-slate-500">Extra monthly pressure</p>
                <p className="mt-2 text-3xl font-semibold text-rose">{formatGBP(scenarioPressure)}</p>
              </div>
              <div className="rounded-md border border-slate-200 p-4">
                <p className="text-sm text-slate-500">Cash left after scenario</p>
                <p className={`mt-2 text-3xl font-semibold ${scenarioCashLeft >= 0 ? "text-teal" : "text-rose"}`}>
                  {formatGBP(scenarioCashLeft)}
                </p>
              </div>
              <div className="rounded-md border border-slate-200 p-4">
                <p className="text-sm text-slate-500">Emergency target time</p>
                <p className="mt-2 text-3xl font-semibold text-ink">{formatMonths(scenarioMonthsToEmergency)}</p>
              </div>
              <div className="rounded-md border border-slate-200 p-4">
                <p className="text-sm text-slate-500">Monthly goal contribution</p>
                <p className="mt-2 text-3xl font-semibold text-ink">
                  {formatGBP(scenarioMonthlyGoalContribution)}
                </p>
              </div>
            </div>
          </section>

          <section className="rounded-md border border-slate-200 bg-panel p-5 shadow-soft lg:col-span-2">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold tracking-normal text-ink">Scenario breakdown</h2>
                <p className="text-sm text-slate-500">How each assumption changes the monthly view</p>
              </div>
              <ReceiptText className="text-teal" size={22} aria-hidden="true" />
            </div>
            <div className="overflow-x-auto rounded-md border border-slate-200">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50 text-left text-xs font-semibold uppercase text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Area</th>
                    <th className="px-4 py-3">Base</th>
                    <th className="px-4 py-3">Assumption</th>
                    <th className="px-4 py-3">Monthly change</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 bg-white">
                  {scenarioRows.map((row) => (
                    <tr key={row.label}>
                      <td className="px-4 py-3 font-medium text-ink">{row.label}</td>
                      <td className="px-4 py-3 text-slate-600">{formatGBP(row.base)}</td>
                      <td className="px-4 py-3 text-slate-600">{row.assumption}</td>
                      <td className="px-4 py-3 font-semibold text-ink">
                        {row.delta >= 0 ? "+" : ""}
                        {formatGBP(row.delta)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      ) : null}
    </main>
  );
}
