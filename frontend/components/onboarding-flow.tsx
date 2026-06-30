"use client";

import { useState } from "react";
import { ArrowRight, Gauge } from "lucide-react";

import type { OnboardingProfile } from "@/types/finscope";

type OnboardingFlowProps = {
  onReady: (profile: OnboardingProfile) => void;
};

const defaultProfile: OnboardingProfile = {
  monthlyIncome: 3240,
  liquidSavings: 6000,
  monthlyDebtPayment: 120,
  rentOrMortgage: 1080,
  investmentBalance: 2500,
  pensionBalance: 12000,
  propertyValue: 0,
  mortgageBalance: 0,
  creditCardBalance: 800,
  loanBalance: 1800,
  averageDebtApr: 19.9,
  emergencyFundTarget: 9000,
  savingsGoalTarget: 15000,
  monthlyGoalContribution: 250
};

type ProfileField = {
  label: string;
  key: keyof OnboardingProfile;
  helper: string;
  suffix?: string;
};

const fieldGroups: Array<{ title: string; intro: string; fields: ProfileField[] }> = [
  {
    title: "Cash flow",
    intro: "The regular monthly numbers I use for the health score.",
    fields: [
      {
        label: "Monthly income",
        key: "monthlyIncome",
        helper: "Salary, freelance income, benefits, and regular income."
      },
      {
        label: "Rent or mortgage",
        key: "rentOrMortgage",
        helper: "Your regular housing payment before other bills."
      },
      {
        label: "Monthly debt payment",
        key: "monthlyDebtPayment",
        helper: "Credit cards, loans, overdrafts, and other monthly debt costs."
      }
    ]
  },
  {
    title: "Assets",
    intro: "Balances I use for net worth and emergency cover.",
    fields: [
      {
        label: "Liquid savings",
        key: "liquidSavings",
        helper: "Cash or easy-access savings you could use in an emergency."
      },
      {
        label: "Investments",
        key: "investmentBalance",
        helper: "ISAs, general investments, or other non-pension investments."
      },
      {
        label: "Pension balance",
        key: "pensionBalance",
        helper: "A rough current pension balance is enough for the dashboard."
      },
      {
        label: "Property value",
        key: "propertyValue",
        helper: "Use 0 if you rent or do not want property included."
      }
    ]
  },
  {
    title: "Debts",
    intro: "Balances I use for payoff and rate-pressure estimates.",
    fields: [
      {
        label: "Mortgage balance",
        key: "mortgageBalance",
        helper: "Use 0 if this does not apply."
      },
      {
        label: "Credit card balance",
        key: "creditCardBalance",
        helper: "Current balance across cards."
      },
      {
        label: "Loan balance",
        key: "loanBalance",
        helper: "Personal loans, car finance, overdraft, or similar debt."
      },
      {
        label: "Average debt APR",
        key: "averageDebtApr",
        helper: "Approximate APR for credit cards and loans.",
        suffix: "%"
      }
    ]
  },
  {
    title: "Goals",
    intro: "Targets I use to make the savings page practical.",
    fields: [
      {
        label: "Emergency target",
        key: "emergencyFundTarget",
        helper: "Your preferred emergency fund target."
      },
      {
        label: "Savings goal",
        key: "savingsGoalTarget",
        helper: "Deposit, travel, car, course fees, or another major target."
      },
      {
        label: "Monthly goal contribution",
        key: "monthlyGoalContribution",
        helper: "How much you expect to put towards these goals each month."
      }
    ]
  }
];

export function OnboardingFlow({ onReady }: OnboardingFlowProps) {
  const [profile, setProfile] = useState<OnboardingProfile>(defaultProfile);

  return (
    <main className="min-h-screen bg-paper px-5 py-8">
      <section className="mx-auto grid max-w-5xl gap-6 rounded-md border border-slate-200 bg-panel p-5 shadow-soft sm:p-6">
        <div className="flex items-start gap-3">
          <Gauge className="mt-1 text-cobalt" size={26} aria-hidden="true" />
          <div>
            <p className="text-sm font-semibold uppercase tracking-normal text-cobalt">FinScope UK</p>
            <h1 className="mt-1 text-2xl font-semibold tracking-normal text-ink">Set your starting position</h1>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Add the numbers the CSV may not show clearly. These feed the health score, scenario snapshot,
              and upload analysis.
            </p>
          </div>
        </div>

        <div className="grid gap-5">
          {fieldGroups.map((group) => (
            <section key={group.title} className="grid gap-4 border-t border-slate-200 pt-5">
              <div>
                <h2 className="text-base font-semibold tracking-normal text-ink">{group.title}</h2>
                <p className="mt-1 text-sm text-slate-500">{group.intro}</p>
              </div>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                {group.fields.map((field) => (
                  <label key={field.key} className="grid gap-2 text-sm font-medium text-slate-600">
                    {field.label}
                    <div className="flex h-11 items-center rounded-md border border-slate-200 bg-white focus-within:border-cobalt">
                      <input
                        className="min-w-0 flex-1 bg-transparent px-3 text-ink outline-none"
                        min="0"
                        step={field.key === "averageDebtApr" ? "0.1" : "1"}
                        type="number"
                        value={profile[field.key]}
                        onChange={(event) =>
                          setProfile((current) => ({
                            ...current,
                            [field.key]: Number(event.target.value)
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
            </section>
          ))}
        </div>

        <button
          className="focus-ring inline-flex h-11 items-center justify-center gap-2 rounded-md bg-ink px-4 text-sm font-semibold text-white"
          type="button"
          onClick={() => onReady(profile)}
        >
          Open dashboard
          <ArrowRight size={18} aria-hidden="true" />
        </button>
      </section>
    </main>
  );
}
