import { apiFetch } from "@/lib/api-client";

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

/** Output of the backend's deterministic FD calculator, passed through unchanged. */
export type FDCalculation = {
  principal: number;
  annual_rate_percent: number;
  tenure_months: number;
  compounding_frequency_per_year: number;
  interest_earned: number;
  maturity_amount: number;
  currency: string;
  calculation_version: string;
  warnings: string[];
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
  calculation?: FDCalculation | null;
  tradeoff?: {
    maturity_difference_vs_highest: number;
    is_highest_calculated_maturity: boolean;
    gains: string[];
    give_ups: string[];
  } | null;
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

const sensitiveField =
  /(\b(?:PAN|Aadhaar|account(?:\s+(?:no\.?|number))?|card(?:\s+(?:no\.?|number))?|CVV|UPI(?:\s+(?:ID|PIN))?|MPIN|OTP|PIN|password)\s*[:=#-]?\s*)([A-Za-z0-9@._+-]+(?:[ -][A-Za-z0-9]+)?)/gi;

/** Redact sensitive values before a query is saved locally or sent to the API. */
export function redactSensitiveInput(query: string): string {
  const labelled = query.replace(sensitiveField, "$1[REDACTED]");
  return labelled
    .replace(/\b[A-Z]{5}\d{4}[A-Z]\b/gi, "[REDACTED]")
    .replace(/\b\d(?:[ -]?\d){11,18}\b/g, (value) =>
      value.replace(/\D/g, "").length >= 12 ? "[REDACTED]" : value,
    )
    .replace(/\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b/g, "[REDACTED]")
    .replace(/\b[\w.-]+@[\w.-]+\b/g, "[REDACTED]");
}

export async function askBankwise(query: string): Promise<AskResponse> {
  const response = await apiFetch("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: redactSensitiveInput(query) }),
  });
  return (await response.json()) as AskResponse;
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
