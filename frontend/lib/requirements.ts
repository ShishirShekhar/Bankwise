import type { AskResponse } from "@/lib/bankwise";
import { formatDuration, formatINR } from "@/lib/bankwise";

export type Requirements = AskResponse["requirements"];

export type RequirementItem = {
  label: string;
  value: string;
  missing: boolean;
};

export const EXAMPLE_GOALS = [
  "I have ₹5 lakh and want to invest for 2 years. I may need the money early.",
  "Where can I put ₹2 lakh in a fixed deposit for 1 year?",
  "I want to deposit ₹10 lakh for 3 years and won't need it before then.",
];

const MISSING_FIELD_PROMPTS: Record<string, string> = {
  amount: "how much you want to deposit (for example ₹5 lakh)",
  duration_months: "how long you want to invest (for example 2 years)",
};

export function missingFieldPrompt(field: string): string {
  return MISSING_FIELD_PROMPTS[field] ?? field.replaceAll("_", " ");
}

function isProvided<T>(value: T | null | undefined): value is T {
  return value !== null && value !== undefined;
}

export function describeRequirements(requirements: Requirements): RequirementItem[] {
  const missing = new Set(requirements.missing ?? []);
  return [
    {
      label: "Product",
      value: requirements.category === "FD" ? "Fixed deposit" : requirements.category,
      missing: false,
    },
    {
      label: "Amount",
      value: isProvided(requirements.amount) ? formatINR(requirements.amount) : "Not provided",
      missing: missing.has("amount") || !isProvided(requirements.amount),
    },
    {
      label: "Duration",
      value: isProvided(requirements.duration_months)
        ? formatDuration(requirements.duration_months)
        : "Not provided",
      missing: missing.has("duration_months") || !isProvided(requirements.duration_months),
    },
    {
      label: "Early access",
      value:
        requirements.liquidity_need === "HIGH" ? "You may need the money early" : "Not mentioned",
      missing: false,
    },
  ];
}
