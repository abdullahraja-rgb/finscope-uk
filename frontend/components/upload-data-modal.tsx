"use client";

import { Download, FileSpreadsheet, Pencil, PlayCircle, Upload, X } from "lucide-react";

type UploadDataModalProps = {
  isAnalysing: boolean;
  open: boolean;
  onClose: () => void;
  onDownloadDemo: () => void;
  onFileSelected: (file: File | undefined) => void;
  onOpenEditor: () => void;
  onUseDemo: () => void;
};

const demoRows = [
  ["Income", "Salary and savings interest"],
  ["Home", "Rent, utilities and council tax"],
  ["Everyday", "Groceries, travel and health"],
  ["Lifestyle", "Subscriptions, eating out and shopping"]
];

export function UploadDataModal({
  isAnalysing,
  open,
  onClose,
  onDownloadDemo,
  onFileSelected,
  onOpenEditor,
  onUseDemo
}: UploadDataModalProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-ink/45 px-4 py-6">
      <section
        aria-labelledby="upload-data-title"
        aria-modal="true"
        className="grid max-h-[92vh] w-full max-w-4xl gap-5 overflow-y-auto rounded-md border border-slate-200 bg-panel p-5 shadow-soft sm:p-6"
        role="dialog"
      >
        <div className="flex items-start justify-between gap-4 border-b border-slate-200 pb-5">
          <div>
            <p className="text-sm font-semibold uppercase text-cobalt">Transaction statement</p>
            <h2 id="upload-data-title" className="mt-1 text-xl font-semibold tracking-normal text-ink">
              Add data to your dashboard
            </h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
              Upload a bank-export CSV, try the complete demo statement, or build your own rows. Every option uses the
              same analysis pipeline.
            </p>
          </div>
          <button
            aria-label="Close upload data"
            className="focus-ring inline-flex h-10 w-10 items-center justify-center rounded-md border border-slate-200 text-slate-600"
            type="button"
            onClick={onClose}
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        <section className="overflow-hidden rounded-md border border-slate-200">
          <div className="flex items-center gap-3 bg-slate-50 px-4 py-3">
            <FileSpreadsheet className="text-cobalt" size={20} aria-hidden="true" />
            <div>
              <h3 className="text-sm font-semibold text-ink">CSV statement</h3>
              <p className="text-xs text-slate-500">Expected columns: date, description, amount, category, transaction_type, account</p>
            </div>
          </div>
          <div className="grid gap-3 p-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
            <p className="text-sm leading-6 text-slate-600">
              Use a CSV export from a bank, or a file following the column format above. Categories can be left blank
              when you want the classifier to fill them in.
            </p>
            <label className="focus-ring inline-flex h-11 cursor-pointer items-center justify-center gap-2 rounded-md bg-ink px-4 text-sm font-semibold text-white transition hover:bg-slate-800">
              <Upload size={18} aria-hidden="true" />
              Choose CSV
              <input
                className="sr-only"
                type="file"
                accept=".csv,text/csv"
                disabled={isAnalysing}
                onChange={(event) => {
                  onFileSelected(event.target.files?.[0]);
                  event.currentTarget.value = "";
                }}
              />
            </label>
          </div>
        </section>

        <section className="overflow-hidden rounded-md border border-cobalt/30 bg-blue-50/50">
          <div className="flex items-center gap-3 border-b border-cobalt/15 px-4 py-3">
            <PlayCircle className="text-cobalt" size={20} aria-hidden="true" />
            <div>
              <h3 className="text-sm font-semibold text-ink">Explore with demo data</h3>
              <p className="text-xs text-slate-500">A realistic 12-month household statement, clearly marked as demo data.</p>
            </div>
          </div>
          <div className="overflow-x-auto px-4 pt-3">
            <table className="min-w-full text-sm">
              <thead className="text-left text-xs font-semibold uppercase text-slate-500">
                <tr>
                  <th className="pb-2 pr-4">Area</th>
                  <th className="pb-2">Included transactions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-cobalt/10 text-slate-600">
                {demoRows.map(([area, detail]) => (
                  <tr key={area}>
                    <td className="py-2 pr-4 font-semibold text-ink">{area}</td>
                    <td className="py-2">{detail}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex flex-col gap-3 p-4 sm:flex-row sm:justify-end">
            <button
              className="focus-ring inline-flex h-11 items-center justify-center gap-2 rounded-md border border-cobalt/25 px-4 text-sm font-semibold text-cobalt"
              type="button"
              onClick={onDownloadDemo}
            >
              <Download size={18} aria-hidden="true" />
              Download demo CSV
            </button>
            <button
              className="focus-ring inline-flex h-11 items-center justify-center gap-2 rounded-md bg-cobalt px-4 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
              disabled={isAnalysing}
              type="button"
              onClick={onUseDemo}
            >
              <PlayCircle size={18} aria-hidden="true" />
              {isAnalysing ? "Analysing demo" : "Use demo data"}
            </button>
          </div>
        </section>

        <section className="grid gap-3 rounded-md border border-slate-200 p-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
          <div>
            <h3 className="text-sm font-semibold text-ink">Build or edit transactions</h3>
            <p className="mt-1 text-sm leading-6 text-slate-500">
              Add rows one at a time, then edit their dates, descriptions, categories, accounts, or amounts before analysis.
            </p>
          </div>
          <button
            className="focus-ring inline-flex h-11 items-center justify-center gap-2 rounded-md border border-slate-200 px-4 text-sm font-semibold text-slate-700"
            type="button"
            onClick={onOpenEditor}
          >
            <Pencil size={18} aria-hidden="true" />
            Open editor
          </button>
        </section>
      </section>
    </div>
  );
}
