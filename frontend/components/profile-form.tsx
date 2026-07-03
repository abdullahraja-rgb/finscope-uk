import { CheckCircle2, RotateCcw } from "lucide-react";

import type { OnboardingProfile } from "@/types/finscope";

export type ProfileSectionId = "cash-flow" | "assets" | "debts" | "goals";

export type ProfileField = {
  helper: string;
  key: keyof OnboardingProfile;
  label: string;
  placeholder: string;
  suffix?: string;
};

export type ProfileFieldGroup = {
  fields: ProfileField[];
  id: ProfileSectionId;
  intro: string;
  title: string;
};

export const emptyProfile: OnboardingProfile = {
  monthlyIncome: 0,
  liquidSavings: 0,
  monthlyDebtPayment: 0,
  rentOrMortgage: 0,
  investmentBalance: 0,
  pensionBalance: 0,
  propertyValue: 0,
  mortgageBalance: 0,
  creditCardBalance: 0,
  loanBalance: 0,
  averageDebtApr: 0,
  emergencyFundTarget: 0,
  savingsGoalTarget: 0,
  monthlyGoalContribution: 0
};

export const profileFieldGroups: ProfileFieldGroup[] = [
  {
    id: "cash-flow",
    title: "Cash flow",
    intro: "The regular monthly numbers I use for the health score.",
    fields: [
      {
        label: "Monthly income",
        key: "monthlyIncome",
        helper: "Salary, freelance income, benefits, and regular income.",
        placeholder: "3200"
      },
      {
        label: "Rent or mortgage",
        key: "rentOrMortgage",
        helper: "Your regular housing payment before other bills.",
        placeholder: "1100"
      },
      {
        label: "Monthly debt payment",
        key: "monthlyDebtPayment",
        helper: "Credit cards, loans, overdrafts, and other monthly debt costs.",
        placeholder: "150"
      }
    ]
  },
  {
    id: "assets",
    title: "Assets",
    intro: "Balances I use for net worth and emergency cover.",
    fields: [
      {
        label: "Liquid savings",
        key: "liquidSavings",
        helper: "Cash or easy-access savings you could use in an emergency.",
        placeholder: "5000"
      },
      {
        label: "Investments",
        key: "investmentBalance",
        helper: "ISAs, general investments, or other non-pension investments.",
        placeholder: "2500"
      },
      {
        label: "Pension balance",
        key: "pensionBalance",
        helper: "A rough current pension balance is enough for the dashboard.",
        placeholder: "12000"
      },
      {
        label: "Property value",
        key: "propertyValue",
        helper: "Use 0 if you rent or do not want property included.",
        placeholder: "0"
      }
    ]
  },
  {
    id: "debts",
    title: "Debts",
    intro: "Balances I use for payoff and rate-pressure estimates.",
    fields: [
      {
        label: "Mortgage balance",
        key: "mortgageBalance",
        helper: "Use 0 if this does not apply.",
        placeholder: "0"
      },
      {
        label: "Credit card balance",
        key: "creditCardBalance",
        helper: "Current balance across cards.",
        placeholder: "800"
      },
      {
        label: "Loan balance",
        key: "loanBalance",
        helper: "Personal loans, car finance, overdraft, or similar debt.",
        placeholder: "1800"
      },
      {
        label: "Average debt APR",
        key: "averageDebtApr",
        helper: "Approximate APR for credit cards and loans.",
        placeholder: "19.9",
        suffix: "%"
      }
    ]
  },
  {
    id: "goals",
    title: "Goals",
    intro: "Targets I use to make the savings page practical.",
    fields: [
      {
        label: "Emergency target",
        key: "emergencyFundTarget",
        helper: "Your preferred emergency fund target.",
        placeholder: "9000"
      },
      {
        label: "Savings goal",
        key: "savingsGoalTarget",
        helper: "Deposit, travel, car, course fees, or another major target.",
        placeholder: "15000"
      },
      {
        label: "Monthly goal contribution",
        key: "monthlyGoalContribution",
        helper: "How much you expect to put towards these goals each month.",
        placeholder: "250"
      }
    ]
  }
];

const profileKeys = profileFieldGroups.flatMap((group) => group.fields.map((field) => field.key));

export function normaliseProfile(value: Partial<Record<keyof OnboardingProfile, unknown>>) {
  return profileKeys.reduce<OnboardingProfile>((profile, key) => {
    const nextValue = Number(value[key]);
    return {
      ...profile,
      [key]: Number.isFinite(nextValue) && nextValue > 0 ? nextValue : 0
    };
  }, emptyProfile);
}

export function profileHasValues(profile: OnboardingProfile) {
  return profileKeys.some((key) => profile[key] > 0);
}

function fieldValue(value: number) {
  return value > 0 ? String(value) : "";
}

function parseFieldValue(value: string) {
  if (value.trim() === "") return 0;
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 0;
}

type ProfileFormProps = {
  cancelLabel?: string;
  highlightedSection?: ProfileSectionId | null;
  onCancel?: () => void;
  onProfileChange: (profile: OnboardingProfile) => void;
  onSave?: () => void;
  profile: OnboardingProfile;
  saveLabel?: string;
  showActions?: boolean;
};

export function ProfileForm({
  cancelLabel = "Cancel",
  highlightedSection,
  onCancel,
  onProfileChange,
  onSave,
  profile,
  saveLabel = "Save profile",
  showActions = true
}: ProfileFormProps) {
  const groups = highlightedSection
    ? [
        ...profileFieldGroups.filter((group) => group.id === highlightedSection),
        ...profileFieldGroups.filter((group) => group.id !== highlightedSection)
      ]
    : profileFieldGroups;

  return (
    <form
      className="grid gap-5"
      onSubmit={(event) => {
        event.preventDefault();
        onSave?.();
      }}
    >
      {groups.map((group) => (
        <section
          key={group.id}
          className={`rounded-md border bg-panel p-5 shadow-soft ${
            highlightedSection === group.id ? "border-cobalt" : "border-slate-200"
          }`}
        >
          <div className="mb-4">
            <h2 className="text-lg font-semibold tracking-normal text-ink">{group.title}</h2>
            <p className="mt-1 text-sm leading-6 text-slate-500">{group.intro}</p>
          </div>
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
                    value={fieldValue(profile[field.key])}
                    onChange={(event) =>
                      onProfileChange({
                        ...profile,
                        [field.key]: parseFieldValue(event.target.value)
                      })
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

      {showActions ? (
        <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          {onCancel ? (
            <button
              className="focus-ring inline-flex h-11 items-center justify-center gap-2 rounded-md border border-slate-200 px-4 text-sm font-semibold text-slate-600"
              type="button"
              onClick={onCancel}
            >
              <RotateCcw size={18} aria-hidden="true" />
              {cancelLabel}
            </button>
          ) : null}
          <button
            className="focus-ring inline-flex h-11 items-center justify-center gap-2 rounded-md bg-ink px-4 text-sm font-semibold text-white"
            type="submit"
          >
            <CheckCircle2 size={18} aria-hidden="true" />
            {saveLabel}
          </button>
        </div>
      ) : null}
    </form>
  );
}
