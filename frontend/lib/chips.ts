export type InsightChip = {
  id: string;
  label: string;
  prompt: string;
};

export function insightChips(year: number, meetingKey?: number): InsightChip[] {
  const circuit = meetingKey != null ? "this circuit" : `${year} (all circuits)`;
  return [
    {
      id: "demo-cpp",
      label: "Ferrari vs McLaren CPP (2023)",
      prompt:
        "Compare Ferrari and McLaren cost-per-point under the cost cap in 2023. Use stored commercial facts.",
    },
    {
      id: "demo-fer",
      label: "Top Driver FER Rankings",
      prompt: `Rank the top drivers by FER (salary per championship point) in ${year}. Use stored salary facts.`,
    },
    {
      id: "demo-1998",
      label: "1998 Telemetry Boundary Test",
      prompt: "Show me the fastest lap telemetry from the 1998 Monaco Grand Prix.",
    },
    {
      id: "cpp",
      label: "Cost / point",
      prompt: `Which constructor has the best cost-per-point in ${year}? Use stored commercial facts, not invented dollars.`,
    },
    {
      id: "fer",
      label: "Driver FER",
      prompt: `Rank the top 5 drivers in ${year} by financial efficiency (salary per championship point).`,
    },
    {
      id: "constructor",
      label: "Constructor after GP",
      prompt: `Explain constructor points and valuation narrative for ${circuit} in ${year}.`,
    },
    {
      id: "dnf",
      label: "DNF / ops risk",
      prompt: `Summarize DNFs as operational and cost risk after ${circuit} in ${year}.`,
    },
    {
      id: "research",
      label: "Look up online",
      prompt: `Look up current constructor valuation estimates online for ${year} and cite sources into the fact store.`,
    },
    {
      id: "hello",
      label: "What can you do?",
      prompt: "What can you do?",
    },
  ];
}
