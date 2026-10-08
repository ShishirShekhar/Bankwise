import type { Source } from "@/lib/bankwise";

export function SourceLink({ source, label }: { source: Source; label?: string }) {
  const text = label || source.title || source.reference || source.type || "Source";
  return source.url ? (
    <a
      href={source.url}
      target="_blank"
      rel="noreferrer"
      className="font-medium text-blue-700 underline decoration-blue-200 underline-offset-2 hover:text-blue-900"
    >
      {text} ↗
    </a>
  ) : (
    <span>{text}</span>
  );
}
