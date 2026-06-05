"use client";

import useSWR from "swr";
import { formatMoney } from "@/lib/utils";

const fetcher = (url) => fetch(url).then((res) => res.json());

export default function Dashboard() {
  // Hardcode month for now or grab from somewhere
  const monthStr = "2026-04";
  const { data: monthData, error, isLoading } = useSWR(`http://127.0.0.1:8000/api/month/${monthStr}`, fetcher);

  if (isLoading) return <div className="p-10 text-[var(--color-text-muted)]">Loading dashboard...</div>;
  if (error) return <div className="p-10 text-[var(--color-error)]">Failed to load data</div>;

  const expenses = monthData?.expenses || [];
  const totalExpenses = expenses.reduce((sum, e) => sum + e.amount, 0);

  return (
    <div>
      <h1 className="font-serif text-3xl font-bold text-[var(--color-text)] mb-8">Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-6 shadow-sm">
          <h2 className="text-[var(--color-text-muted)] text-sm font-bold uppercase tracking-wider mb-2">Total Expenses</h2>
          <div className="font-mono text-3xl font-bold text-[var(--color-expense)]">
            - {totalExpenses.toLocaleString('pl-PL', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} PLN
          </div>
        </div>
      </div>
    </div>
  );
}
