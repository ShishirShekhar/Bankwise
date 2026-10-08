import { SourceLink } from "@/components/compare/SourceLink";
import type { AskResponse } from "@/lib/bankwise";

export function SkippedProducts({ products }: { products: AskResponse["skipped"] }) {
  if (!products.length) return null;
  return (
    <section className="mt-9 rounded-2xl border border-amber-200 bg-white p-6">
      <h2 className="text-lg font-semibold">Products excluded from this comparison</h2>
      <p className="mt-1 text-sm text-gray-500">
        These products were not used for calculations because their available data did not meet the
        request.
      </p>
      <ul className="mt-4 space-y-4">
        {products.map((product) => (
          <li key={product.bank} className="border-t border-gray-100 pt-4 text-sm">
            <p>
              <span className="font-semibold">{product.bank}:</span> {product.reason}
            </p>
            {product.conflicts?.length ? (
              <p className="mt-1 font-medium text-amber-800">
                A source conflict is recorded for this product.
              </p>
            ) : null}
            {product.sources?.length ? (
              <p className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-gray-500">
                Sources:{" "}
                {product.sources.map((source, index) => (
                  <span key={source.id || index}>
                    <SourceLink source={source} />
                  </span>
                ))}
              </p>
            ) : null}
          </li>
        ))}
      </ul>
    </section>
  );
}
