export type DecisionSection = {
  title: string;
  content: string;
};

const headings = [
  { label: "Executive Decision Summary", title: "Executive Decision Summary" },
  { label: "The Key Trade-off", title: "The Key Trade-off" },
  { label: "Conditions & Transparency", title: "Conditions & Transparency" },
  { label: "Critical Conditions & Transparency", title: "Conditions & Transparency" },
];

function normalizeMarkdown(text: string): string {
  return text.replace(/\\([*_])/g, "$1");
}

function headingForLine(line: string): { title: string; remainder: string } | null {
  const match = line.match(
    /^\s*(?:#{1,3}\s*)?(?:\*{1,2})?(?:[1-3]\.\s*)?(?:\*{1,2})?(Executive Decision Summary|The Key Trade-off(?:\s*\([^\n]*\))?|Conditions & Transparency|Critical Conditions & Transparency)(?:\*{1,2})?\s*:?\s*(.*)$/i,
  );
  if (!match) return null;
  const matchedHeading = match[1] ?? "";
  const heading = headings.find(({ label }) => matchedHeading.startsWith(label));
  return heading ? { title: heading.title, remainder: match[2] ?? "" } : null;
}

export function parseDecisionExplanation(explanation: string): DecisionSection[] {
  const lines = normalizeMarkdown(explanation).split("\n");
  const sections: DecisionSection[] = [];
  let currentTitle: string | null = null;
  let currentLines: string[] = [];
  const introductoryLines: string[] = [];

  function saveCurrentSection() {
    if (currentTitle) {
      sections.push({ title: currentTitle, content: currentLines.join("\n").trim() });
    }
    currentLines = [];
  }

  for (const line of lines) {
    const heading = headingForLine(line);
    if (heading) {
      saveCurrentSection();
      currentTitle = heading.title;
      if (heading.remainder) currentLines.push(heading.remainder);
    } else if (currentTitle) {
      currentLines.push(line);
    } else {
      introductoryLines.push(line);
    }
  }

  saveCurrentSection();

  const introduction = introductoryLines.join("\n").trim();
  if (introduction) sections.unshift({ title: "Overview", content: introduction });
  return sections.length
    ? sections
    : [{ title: "Explanation", content: normalizeMarkdown(explanation).trim() }];
}
