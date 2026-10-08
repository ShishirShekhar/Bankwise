import type { AskOption } from "@/lib/bankwise";

export function selectTradeoffOptions(options: AskOption[]) {
  const highestMaturity =
    options.find((option) => option.tradeoff?.is_highest_calculated_maturity) ?? options[0];
  const lowerPenalty = options.find((option) =>
    option.tradeoff?.gains.some((gain) => gain.toLowerCase().includes("lower exit penalty")),
  );
  const alternative = lowerPenalty ?? options.find((option) => option !== highestMaturity);

  return { highestMaturity, alternative };
}
