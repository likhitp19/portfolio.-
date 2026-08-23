import type { StandingsProgression } from "@/lib/types";

export type ChartRow = {
  circuit: string;
  meeting_key: number;
  [driver: string]: string | number;
};

export function progressionToChartRows(data: StandingsProgression): ChartRow[] {
  return data.circuits.map((circuit, index) => {
    const row: ChartRow = {
      circuit: circuit.name,
      meeting_key: circuit.meeting_key,
    };
    for (const series of data.series) {
      row[series.driver] = series.points[index] ?? 0;
    }
    return row;
  });
}
