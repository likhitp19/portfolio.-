export type MarkdownTable = {
  headers: string[];
  rows: string[][];
};

export type CopilotLayers = {
  summary: string;
  deepDive: string;
  tables: MarkdownTable[];
};

const SENTENCE = /(?<=[.!?])\s+/;

export function splitCopilotLayers(answer: string, fallbackSummary?: string): CopilotLayers {
  const text = answer.trim();
  if (!text) {
    return { summary: fallbackSummary || "No briefing produced.", deepDive: "", tables: [] };
  }
  const paragraphs = text.split(/\n\s*\n/).map((part) => part.trim()).filter(Boolean);
  const lead = paragraphs[0] ?? text;
  const sentences = lead.split(SENTENCE).map((part) => part.trim()).filter(Boolean);
  const summary = (fallbackSummary || sentences.slice(0, 2).join(" ")).trim();
  const leftover = sentences.slice(2).join(" ");
  const deepParts = [...(leftover ? [leftover] : []), ...paragraphs.slice(1)];
  const deepDive = deepParts.join("\n\n").trim() || text;
  return { summary, deepDive, tables: extractMarkdownTables(deepDive) };
}

export function extractMarkdownTables(markdown: string): MarkdownTable[] {
  const tables: MarkdownTable[] = [];
  const blocks = markdown.split(/\n{2,}/);
  for (const block of blocks) {
    const lines = block
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line.startsWith("|"));
    if (lines.length < 3) {
      continue;
    }
    const parsed = lines.map((line) =>
      line
        .replace(/^\|/, "")
        .replace(/\|$/, "")
        .split("|")
        .map((cell) => cell.trim()),
    );
    const [headers, divider, ...rows] = parsed;
    if (!headers || !divider || !rows.length) {
      continue;
    }
    if (!divider.every((cell) => /^:?-+:?$/.test(cell.replace(/\s/g, "")))) {
      continue;
    }
    tables.push({ headers, rows });
  }
  return tables;
}

export function numericSeriesFromTables(tables: MarkdownTable[]): { label: string; value: number }[] {
  const series: { label: string; value: number }[] = [];
  for (const table of tables) {
    const valueIndex = table.headers.findIndex((header, index) => {
      if (index === 0) {
        return false;
      }
      return table.rows.some((row) => Number.isFinite(parseNumeric(row[index] ?? "")));
    });
    if (valueIndex < 0) {
      continue;
    }
    for (const row of table.rows) {
      const value = parseNumeric(row[valueIndex] ?? "");
      const label = row[0] ?? "";
      if (label && value != null) {
        series.push({ label, value });
      }
    }
  }
  return series;
}

function parseNumeric(raw: string): number | null {
  const cleaned = raw.replace(/[$,]/g, "").replace(/%$/, "").trim();
  if (!cleaned) {
    return null;
  }
  const value = Number(cleaned);
  return Number.isFinite(value) ? value : null;
}
