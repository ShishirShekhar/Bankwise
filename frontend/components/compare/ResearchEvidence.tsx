import { SourceLink } from "@/components/compare/SourceLink";
import type { AskResponse, Source } from "@/lib/bankwise";

export function ResearchEvidence({ research }: { research: AskResponse["research"] }) {
  if (!research) return null;
  const chunks = research.rag_chunks ?? [];
  const searchSources = research.search_sources ?? [];
  const serviceFailed =
    research.rag_status?.startsWith("failed") ||
    research.search_status?.startsWith("failed") ||
    research.search_status === "rag_failed" ||
    research.search_status === "no_grounded_sources" ||
    research.search_status === "rag_unavailable" ||
    research.search_status === "unavailable";
  if (!chunks.length && !searchSources.length && !serviceFailed) return null;

  return (
    <section className="mt-8 rounded-2xl border border-blue-200 bg-white p-6">
      <h2 className="text-lg font-semibold text-gray-900">Research evidence</h2>
      <p className="mt-1 text-sm leading-6 text-gray-600">
        These retrieved excerpts and search citations are evidence for review. They were not used as
        financial inputs; calculations use only verified catalogue records.
      </p>
      {serviceFailed ? (
        <p role="status" className="mt-3 rounded-lg bg-amber-50 p-3 text-sm text-amber-900">
          Some current research services were unavailable. No search-dependent fact was treated as
          verified; any calculations use eligible catalogue records only.
        </p>
      ) : null}
      {chunks.length ? (
        <ul className="mt-4 space-y-4">
          {chunks.map((chunk) => {
            const source: Source = {
              id: chunk.chunk_id,
              title: chunk.title,
              url: chunk.canonical_url,
              retrieved_at: chunk.retrieved_at,
              verification_status: chunk.verification_status,
            };
            return (
              <li key={chunk.chunk_id} className="rounded-xl bg-gray-50 p-4">
                <p className="text-sm leading-6 text-gray-700">{chunk.excerpt}</p>
                <p className="mt-2 flex flex-wrap items-center gap-x-3 text-xs text-gray-500">
                  <SourceLink source={source} />
                  <span>Source status: {chunk.verification_status}</span>
                </p>
              </li>
            );
          })}
        </ul>
      ) : null}
      {searchSources.length ? (
        <div className="mt-4">
          <h3 className="text-sm font-semibold text-gray-800">
            Google Search citations · pending verification
          </h3>
          <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-2 text-sm">
            {searchSources.map((source, index) => (
              <li key={source.id ?? source.url ?? index}>
                <SourceLink source={source} />
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
