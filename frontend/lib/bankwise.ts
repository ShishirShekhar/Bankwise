export type Source = {
  id?: string;
  type?: string;
  title?: string | null;
  reference?: string | null;
  url?: string | null;
  retrieved_at?: string | null;
  verified_at?: string | null;
  effective_from?: string | null;
  effective_to?: string | null;
  confidence?: string | null;
  verification_status?: string | null;
  freshness?: string | null;
};

export type AskOption = {
  bank: string;
  product_name: string;
  rate_percent: number;
  maturity_amount: number | null;
  interest_earned: number | null;
  early_exit_amount: number | null;
  early_exit_note: string | null;
  rate: string;
  maturity: string;
  interest: string;
  flexibility: string;
  penalty: string;
  verified: string;
  tag: string;
  calculation_note: string | null;
  source: Source;
  calculation_source_url: string | null;
  penalty_source_url: string | null;
};

export type AskResponse = {
  status: "OK" | "NEEDS_CLARIFICATION" | "UNSUPPORTED" | "NO_MATCH";
  message: string | null;
  requirements: {
    category: string;
    amount: number | null;
    duration_months: number | null;
    liquidity_need: string | null;
    missing: string[];
  };
  options: AskOption[];
  skipped: Array<{
    bank: string;
    reason: string;
    sources?: Source[];
    conflicts?: Array<Record<string, unknown>>;
  }>;
  explanation: string;
  warnings: string[];
  sources: Source[];
  request_id?: string;
};

const API_BASE_URL = (process.env.NEXT_PUBLIC_BANKWISE_API_URL || "http://localhost:8080").replace(
  /\/$/,
  "",
);

export async function askBankwise(query: string): Promise<AskResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
  } catch {
    throw new Error(
      `Could not reach BankWise API at ${API_BASE_URL}. Check that the backend is running.`,
    );
  }

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(payload?.detail || payload?.message || `Request failed (${response.status}).`);
  }
  return payload as AskResponse;
}

export function formatINR(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "Unavailable";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatDuration(months: number | null): string {
  if (months === null) return "Duration not provided";
  const years = Math.floor(months / 12);
  const remainingMonths = months % 12;
  const parts = [];
  if (years) parts.push(`${years} ${years === 1 ? "year" : "years"}`);
  if (remainingMonths)
    parts.push(`${remainingMonths} ${remainingMonths === 1 ? "month" : "months"}`);
  return parts.join(" ") || `${months} months`;
}

export function resultSourceLabel(source: Source): string {
  return source.title || source.reference || source.type || "Product source";
}
