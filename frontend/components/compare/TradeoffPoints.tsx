export function TradeoffPoints({ gains, giveUps }: { gains: string[]; giveUps: string[] }) {
  return (
    <div className="mt-4 grid gap-3">
      <TradeoffList
        title="What you gain"
        items={gains}
        tone="gain"
        emptyMessage="No deterministic gain details were returned."
      />
      <TradeoffList
        title="What you give up"
        items={giveUps}
        tone="give-up"
        emptyMessage="No deterministic give-up details were returned."
      />
    </div>
  );
}

function TradeoffList({
  title,
  items,
  tone,
  emptyMessage,
}: {
  title: string;
  items: string[];
  tone: "gain" | "give-up";
  emptyMessage: string;
}) {
  const isGain = tone === "gain";
  return (
    <div className={`rounded-xl p-3 ${isGain ? "bg-green-50" : "bg-amber-50"}`}>
      <p
        className={`text-xs font-semibold tracking-wide uppercase ${isGain ? "text-green-800" : "text-amber-800"}`}
      >
        {title}
      </p>
      <ul className={`mt-2 space-y-1 text-sm ${isGain ? "text-green-900" : "text-amber-900"}`}>
        {items.length ? (
          items.map((item) => (
            <li key={item}>
              {isGain ? "✓" : "−"} {item}
            </li>
          ))
        ) : (
          <li>{emptyMessage}</li>
        )}
      </ul>
    </div>
  );
}
