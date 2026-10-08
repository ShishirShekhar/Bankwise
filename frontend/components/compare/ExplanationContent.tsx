import { Fragment, type ReactNode } from "react";

function renderInline(text: string): ReactNode[] {
  return text.split(/(\*\*.+?\*\*)/g).map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={index} className="font-semibold text-gray-900">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return <Fragment key={index}>{part}</Fragment>;
  });
}

function parseBullet(line: string): { text: string; indent: number } | null {
  const match = line.match(/^(\s*)(?:\\?[*•-]|\d+[.)])\s+(.*)$/);
  if (!match) return null;
  return {
    text: match[2] ?? "",
    indent: Math.min(Math.floor((match[1] ?? "").length / 2), 4),
  };
}

export function ExplanationContent({ content }: { content: string }) {
  const blocks = content
    .trim()
    .split(/\n\s*\n/)
    .filter(Boolean);

  return (
    <div className="space-y-4 text-sm leading-7 text-gray-700">
      {blocks.map((block, blockIndex) => {
        const lines = block.split("\n");
        const listItems = lines.map(parseBullet);
        if (listItems.every((item) => item !== null)) {
          return (
            <ul key={blockIndex} className="list-disc space-y-2 pl-5 marker:text-blue-500">
              {listItems.map(
                (item, itemIndex) =>
                  item && (
                    <li
                      key={`${blockIndex}-${itemIndex}`}
                      style={{ marginLeft: `${item.indent * 0.75}rem` }}
                    >
                      {renderInline(item.text)}
                    </li>
                  ),
              )}
            </ul>
          );
        }

        return (
          <p key={blockIndex}>
            {lines.map((line, lineIndex) => (
              <Fragment key={lineIndex}>
                {lineIndex > 0 && <br />}
                {renderInline(line)}
              </Fragment>
            ))}
          </p>
        );
      })}
    </div>
  );
}
