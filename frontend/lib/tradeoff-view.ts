import type { AskOption } from "@/lib/bankwise";

export function selectTradeoffOptions(options: AskOption[]) {
  const calculatedOptions = options.filter((option) => option.maturity_amount !== null);
  const highestMaturity =
    calculatedOptions.find((option) => option.tradeoff?.is_highest_calculated_maturity) ??
    calculatedOptions[0];
  const lowerPenalty = calculatedOptions.find((option) =>
    option.tradeoff?.gains.some((gain) => gain.toLowerCase().includes("lower exit penalty")),
  );
  const alternative =
    lowerPenalty ?? calculatedOptions.find((option) => option !== highestMaturity);

  return { highestMaturity, alternative };
}
