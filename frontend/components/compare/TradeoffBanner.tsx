import type { AskOption } from "@/lib/bankwise";

export function TradeoffBanner({
  topOption,
  alternative,
}: {
  topOption: AskOption;
  alternative: AskOption;
}) {
  const hasPenaltyAdvantage = alternative.tradeoff?.gains.some((gain) =>
    gain.toLowerCase().includes("lower exit penalty"),
  );
  return (
    <section
      className="mt-7 rounded-3xl border border-indigo-200 bg-white p-6 shadow-sm sm:p-8"
      aria-labelledby="tradeoff-heading"
    >
      <p className="text-xs font-semibold tracking-[0.15em] text-indigo-700 uppercase">
        What am I giving up?
      </p>
      <h2 id="tradeoff-heading" className="mt-2 text-2xl font-semibold">
        Return and flexibility, side by side
      </h2>
      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <TradeoffOption
          label="Option A · Highest calculated maturity"
          option={topOption}
          tone="gain"
        />
        <TradeoffOption
          label={
            hasPenaltyAdvantage ? "Option B · Lower exit penalty" : "Option B · Alternative option"
          }
          option={alternative}
          tone="give-up"
        />
      </div>
    </section>
  );
}

function TradeoffOption({
  label,
  option,
  tone,
}: {
  label: string;
  option: AskOption;
  tone: "gain" | "give-up";
}) {
  const classes = tone === "gain" ? "bg-green-50" : "bg-amber-50";
  return (
    <article className={`rounded-2xl p-5 ${classes}`}>
      <h3 className="text-sm font-semibold text-gray-800">{label}</h3>
      <p className="mt-1 text-lg font-semibold text-gray-900">
        {option.bank} · {option.maturity}
      </p>
      <TradeoffLines title="Gains" items={option.tradeoff?.gains ?? []} positive />
      <TradeoffLines title="Give-ups" items={option.tradeoff?.give_ups ?? []} />
      <p className="mt-3 text-sm text-gray-700">
        Withdrawal terms: {option.early_exit_note || option.penalty}
      </p>
    </article>
  );
}

function TradeoffLines({
  title,
  items,
  positive = false,
}: {
  title: string;
  items: string[];
  positive?: boolean;
}) {
  return (
    <div className="mt-3">
      <p className="text-xs font-semibold text-gray-600">{title}</p>
      {items.length ? (
        <ul className={`mt-1 space-y-1 text-sm ${positive ? "text-green-900" : "text-amber-900"}`}>
          {items.map((item) => (
            <li key={item}>
              {positive ? "✓" : "−"} {item}
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-1 text-sm text-gray-500">No deterministic details returned.</p>
      )}
    </div>
  );
}
