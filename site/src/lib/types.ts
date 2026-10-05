// What /api/dashboard returns (see src/markethub/dashboard.py).
export type N = number | null;
type Facts = { return_1m: N; return_3m: N; return_ytd: N; return_1y: N; spark: number[] };
export type Row = Facts & {
  ticker: string; name: string; sector: string; shares: number; avg_cost: N; price: N; value: N; cost: N;
  pnl: N; pnl_pct: N; day_change: N; day_change_pct: N; weight: N;
};
export type Watch = Facts & { ticker: string; name: string; price: N; day_change_pct: N; from_high_52w: N; year_low: N; year_high: N };
export type Dashboard = {
  totals: { value: N; cost: N; pnl: N; pnl_pct: N; day_change: N; day_change_pct: N; positions: number; cost_covers: number };
  positions: Row[];
  sectors: { sector: string; value: number; weight: number }[];
  history: { dates: string[]; value: number[]; portfolio_rebased: number[]; benchmark_rebased: number[]; benchmark?: string };
  watchlist: Watch[];
  movers: { up: string[]; down: string[] };
  benchmark: Facts & { ticker: string; price: N; day_change_pct: N };
  notes: string[];
};
