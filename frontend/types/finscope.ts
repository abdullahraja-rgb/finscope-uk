export type Metric = {
  label: string;
  value: string;
  delta: string;
  tone: "good" | "watch" | "risk" | "neutral";
};

export type CategorySpend = {
  category: string;
  spend: number;
  forecast: number;
};

export type InflationImpact = {
  category: string;
  personal: number;
  national: number;
};
