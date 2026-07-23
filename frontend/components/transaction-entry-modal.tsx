"use client";

import { FormEvent, useEffect, useState } from "react";
import { Pencil, Plus, Trash2, X } from "lucide-react";

import type { TransactionPayload } from "@/types/finscope";

type TransactionEntryModalProps = {
  open: boolean;
  rows: TransactionPayload[];
  isAnalysing: boolean;
  initialDraft?: TransactionDraftPreset | null;
  intro?: string;
  title?: string;
  onClose: () => void;
  onRowsChange: (rows: TransactionPayload[]) => void;
  onAnalyse: (rows: TransactionPayload[]) => Promise<void>;
};

export type TransactionDraftPreset = Partial<{
  date: string;
  description: string;
  amount: string;
  category: string;
  transaction_type: string;
  account: string;
}>;

const categories = [
  "groceries",
  "eating_out",
  "transport",
  "housing",
  "utilities",
  "subscriptions",
  "shopping",
  "health",
  "income"
];

const accounts = ["current", "credit_card", "savings"];

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

function displayCategory(category: string | null | undefined) {
  if (!category) return "Uncategorised";
  return category
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function blankDraft() {
  return {
    date: todayIsoDate(),
    description: "",
    amount: "",
    category: "groceries",
    transaction_type: "expense",
    account: "current"
  };
}

export function TransactionEntryModal({
  open,
  rows,
  isAnalysing,
  initialDraft,
  intro = "Each saved row is converted into the same CSV format as an upload.",
  title = "Add rows without a CSV",
  onClose,
  onRowsChange,
  onAnalyse
}: TransactionEntryModalProps) {
  const [draft, setDraft] = useState(blankDraft());
  const [editingRowIndex, setEditingRowIndex] = useState<number | null>(null);
  const amount = Number(draft.amount);
  const canAdd = draft.date.trim() !== "" && draft.description.trim() !== "" && Number.isFinite(amount) && amount > 0;

  useEffect(() => {
    if (!open) return;
    setEditingRowIndex(null);
    setDraft((current) => ({
      ...current,
      ...initialDraft,
      date: initialDraft?.date ?? current.date ?? todayIsoDate()
    }));
  }, [initialDraft, open]);

  if (!open) return null;

  function updateDraft(key: keyof ReturnType<typeof blankDraft>, value: string) {
    setDraft((current) => {
      const next = { ...current, [key]: value };
      if (key === "transaction_type" && value === "income") {
        next.category = "income";
      }
      if (key === "transaction_type" && value === "expense" && current.category === "income") {
        next.category = "groceries";
      }
      return next;
    });
  }

  function addRow(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canAdd) return;

    const signedAmount = draft.transaction_type === "income" ? Math.abs(amount) : -Math.abs(amount);
    const nextRow: TransactionPayload = {
      date: draft.date,
      description: draft.description.trim(),
      amount: signedAmount,
      category: draft.category,
      transaction_type: draft.transaction_type,
      account: draft.account
    };

    if (editingRowIndex === null) {
      onRowsChange([...rows, nextRow]);
    } else {
      onRowsChange(rows.map((row, index) => (index === editingRowIndex ? nextRow : row)));
      setEditingRowIndex(null);
    }
    setDraft({
      ...blankDraft(),
      date: draft.date,
      transaction_type: draft.transaction_type,
      category: draft.transaction_type === "income" ? "income" : "groceries",
      account: draft.account
    });
  }

  function removeRow(index: number) {
    onRowsChange(rows.filter((_, rowIndex) => rowIndex !== index));
    if (editingRowIndex === index) {
      setEditingRowIndex(null);
      setDraft(blankDraft());
    }
  }

  function editRow(index: number) {
    const row = rows[index];
    setEditingRowIndex(index);
    setDraft({
      date: row.date,
      description: row.description,
      amount: Math.abs(row.amount).toFixed(2),
      category: row.category ?? "groceries",
      transaction_type: row.transaction_type ?? (row.amount >= 0 ? "income" : "expense"),
      account: row.account ?? "current"
    });
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-ink/45 px-4 py-6">
      <section
        aria-modal="true"
        className="grid max-h-[92vh] w-full max-w-5xl gap-5 overflow-y-auto rounded-md border border-slate-200 bg-panel p-5 shadow-soft"
        role="dialog"
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-semibold uppercase text-cobalt">Transaction entry</p>
            <h2 className="mt-1 text-xl font-semibold tracking-normal text-ink">{title}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">{intro}</p>
          </div>
          <button
            className="focus-ring inline-flex h-10 w-10 items-center justify-center rounded-md border border-slate-200 text-slate-600"
            type="button"
            onClick={onClose}
          >
            <X size={18} aria-hidden="true" />
            <span className="sr-only">Close</span>
          </button>
        </div>

        <form className="grid gap-4 rounded-md border border-slate-200 p-4" onSubmit={addRow}>
          <div className="grid gap-4 md:grid-cols-3">
            <label className="grid gap-2 text-sm font-medium text-slate-600">
              Date
              <input
                className="h-11 rounded-md border border-slate-200 bg-white px-3 text-ink outline-none focus:border-cobalt"
                type="date"
                value={draft.date}
                onChange={(event) => updateDraft("date", event.target.value)}
              />
            </label>
            <label className="grid gap-2 text-sm font-medium text-slate-600 md:col-span-2">
              Title
              <input
                className="h-11 rounded-md border border-slate-200 bg-white px-3 text-ink outline-none focus:border-cobalt"
                placeholder="Tesco, Netflix, Salary Payroll"
                type="text"
                value={draft.description}
                onChange={(event) => updateDraft("description", event.target.value)}
              />
            </label>
          </div>

          <div className="grid gap-4 md:grid-cols-4">
            <label className="grid gap-2 text-sm font-medium text-slate-600">
              Type
              <select
                className="h-11 rounded-md border border-slate-200 bg-white px-3 text-ink outline-none focus:border-cobalt"
                value={draft.transaction_type}
                onChange={(event) => updateDraft("transaction_type", event.target.value)}
              >
                <option value="expense">Expense</option>
                <option value="income">Income</option>
                <option value="transfer">Transfer</option>
              </select>
            </label>
            <label className="grid gap-2 text-sm font-medium text-slate-600">
              Category
              <select
                className="h-11 rounded-md border border-slate-200 bg-white px-3 text-ink outline-none focus:border-cobalt"
                value={draft.category}
                onChange={(event) => updateDraft("category", event.target.value)}
              >
                {categories.map((category) => (
                  <option key={category} value={category}>
                    {displayCategory(category)}
                  </option>
                ))}
              </select>
            </label>
            <label className="grid gap-2 text-sm font-medium text-slate-600">
              Amount
              <input
                className="h-11 rounded-md border border-slate-200 bg-white px-3 text-ink outline-none focus:border-cobalt"
                min="0"
                placeholder="45.50"
                step="0.01"
                type="number"
                value={draft.amount}
                onChange={(event) => updateDraft("amount", event.target.value)}
              />
            </label>
            <label className="grid gap-2 text-sm font-medium text-slate-600">
              Account
              <select
                className="h-11 rounded-md border border-slate-200 bg-white px-3 text-ink outline-none focus:border-cobalt"
                value={draft.account}
                onChange={(event) => updateDraft("account", event.target.value)}
              >
                {accounts.map((account) => (
                  <option key={account} value={account}>
                    {displayCategory(account)}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <button
            className="focus-ring inline-flex h-11 items-center justify-center gap-2 rounded-md border border-slate-200 px-4 text-sm font-semibold text-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={!canAdd}
            type="submit"
          >
            <Plus size={18} aria-hidden="true" />
            {editingRowIndex === null ? "Add row" : "Save changes"}
          </button>
        </form>

        <section className="grid gap-3">
          <div className="flex items-center justify-between gap-3">
            <h3 className="text-base font-semibold tracking-normal text-ink">Rows ready to analyse</h3>
            <span className="text-sm font-medium text-slate-500">{rows.length} rows</span>
          </div>
          {rows.length > 0 ? (
            <div className="overflow-x-auto rounded-md border border-slate-200">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50 text-left text-xs font-semibold uppercase text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Date</th>
                    <th className="px-4 py-3">Title</th>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3">Category</th>
                    <th className="px-4 py-3">Amount</th>
                    <th className="px-4 py-3">Edit</th>
                    <th className="px-4 py-3">Remove</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 bg-white">
                  {rows.map((row, index) => (
                    <tr key={`${row.date}-${row.description}-${index}`}>
                      <td className="px-4 py-3 text-slate-600">{row.date}</td>
                      <td className="px-4 py-3 font-medium text-ink">{row.description}</td>
                      <td className="px-4 py-3 text-slate-600">{displayCategory(row.transaction_type)}</td>
                      <td className="px-4 py-3 text-slate-600">{displayCategory(row.category)}</td>
                      <td className="px-4 py-3 font-semibold text-ink">GBP {Math.abs(row.amount).toFixed(2)}</td>
                      <td className="px-4 py-3">
                        <button
                          className="focus-ring inline-flex h-9 w-9 items-center justify-center rounded-md border border-slate-200 text-cobalt"
                          type="button"
                          onClick={() => editRow(index)}
                        >
                          <Pencil size={16} aria-hidden="true" />
                          <span className="sr-only">Edit row</span>
                        </button>
                      </td>
                      <td className="px-4 py-3">
                        <button
                          className="focus-ring inline-flex h-9 w-9 items-center justify-center rounded-md border border-slate-200 text-rose"
                          type="button"
                          onClick={() => removeRow(index)}
                        >
                          <Trash2 size={16} aria-hidden="true" />
                          <span className="sr-only">Remove row</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="rounded-md border border-dashed border-slate-300 p-5 text-sm text-slate-500">
              Add at least one transaction row to run the dashboard analysis.
            </div>
          )}
        </section>

        <div className="flex flex-col-reverse gap-3 border-t border-slate-200 pt-5 sm:flex-row sm:justify-end">
          <button
            className="focus-ring inline-flex h-11 items-center justify-center rounded-md border border-slate-200 px-4 text-sm font-semibold text-slate-600"
            type="button"
            onClick={onClose}
          >
            Close
          </button>
          <button
            className="focus-ring inline-flex h-11 items-center justify-center gap-2 rounded-md bg-ink px-4 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
            disabled={rows.length === 0 || isAnalysing}
            type="button"
            onClick={() => {
              void onAnalyse(rows);
            }}
          >
            <Plus size={18} aria-hidden="true" />
            {isAnalysing ? "Analysing" : "Analyse rows"}
          </button>
        </div>
      </section>
    </div>
  );
}
