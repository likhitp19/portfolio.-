export type InsightChip = {
  id: string;
  label: string;
  prompt: string;
};

export function insightChips(_year: number, _meetingKey?: number): InsightChip[] {
  return [
    {
      id: "fer-2024",
      label: "2024 driver FER",
      prompt: "Rank 2024 drivers by Financial Efficiency Rating (FER)",
    },
    {
      id: "cpp-2023",
      label: "McLaren vs Ferrari CPP",
      prompt: "Compare McLaren vs Ferrari Cost-Per-Point in 2023",
    },
    {
      id: "fia-cap",
      label: "FIA cost cap",
      prompt: "Explain FIA Cost Cap regulations and breach penalties",
    },
  ];
}
