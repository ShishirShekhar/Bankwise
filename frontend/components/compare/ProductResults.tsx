import { ProductCard } from "@/components/compare/ProductCard";
import type { AskOption } from "@/lib/bankwise";

export function ProductResults({
  options,
  onSelect,
}: {
  options: AskOption[];
  onSelect: (option: AskOption) => void;
}) {
  if (!options.length) return null;
  return (
    <section className="mt-10">
      <div className="mb-5 flex items-center justify-between">
        <h2 className="text-xl font-semibold">
          {options.length} verified {options.length === 1 ? "option" : "options"}
        </h2>
        <span className="text-sm text-gray-500">Ordered by estimated maturity</span>
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        {options.map((option, index) => (
          <ProductCard
            key={`${option.bank}-${option.product_name}`}
            option={option}
            featured={index === 0}
            onViewDetails={() => onSelect(option)}
          />
        ))}
      </div>
    </section>
  );
}
