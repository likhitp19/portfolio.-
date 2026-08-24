import type { ConstructorStanding } from "@/lib/types";

export const FIA_COST_CAP_USD = 135_000_000;

const TEAM_CODES: Record<string, string> = {
  mclaren: "MCL",
  ferrari: "FER",
  "red bull": "RBR",
  mercedes: "MER",
  "aston martin": "AST",
  alpine: "ALP",
  williams: "WIL",
  haas: "HAS",
  rb: "VCB",
  "racing bulls": "VCB",
  "visa cash": "VCB",
  sauber: "SAU",
  "kick sauber": "SAU",
  alphatauri: "AT",
  alfa: "SAU",
};

export type CppBand = "efficient" | "neutral" | "warning" | "inefficient";

export function constructorCode(teamName: string): string {
  const key = teamName.toLowerCase();
  for (const [alias, code] of Object.entries(TEAM_CODES)) {
    if (key.includes(alias)) {
      return code;
    }
  }
  return teamName
    .replace(/Racing|Team|F1/g, "")
    .trim()
    .slice(0, 3)
    .toUpperCase();
}

export function cppBand(cpp: number, average: number): CppBand {
  if (!(average > 0)) {
    return "neutral";
  }
  const ratio = cpp / average;
  if (ratio <= 0.75) {
    return "efficient";
  }
  if (ratio <= 1.05) {
    return "neutral";
  }
  if (ratio <= 1.25) {
    return "warning";
  }
  return "inefficient";
}

export function cppBandColor(band: CppBand): { fill: string; stroke: string } {
  switch (band) {
    case "efficient":
      return { fill: "rgba(16, 185, 129, 0.35)", stroke: "#10B981" };
    case "warning":
      return { fill: "rgba(245, 158, 11, 0.28)", stroke: "#F59E0B" };
    case "inefficient":
      return { fill: "rgba(225, 6, 0, 0.35)", stroke: "#E10600" };
    default:
      return { fill: "rgba(42, 42, 42, 0.9)", stroke: "#3F3F46" };
  }
}

export type ManufacturerKpis = {
  totalGridValuation: number | null;
  avgCap: number | null;
  capUtilization: number | null;
  avgCpp: number | null;
  inefficiency: number | null;
  inefficiencyLabel: "TIGHT" | "ELEVATED" | "HIGH";
  efficient: ConstructorStanding | null;
  leader: ConstructorStanding | null;
  yieldShare: number | null;
};

function mean(values: number[]): number | null {
  if (!values.length) {
    return null;
  }
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

export function manufacturerKpis(rows: ConstructorStanding[]): ManufacturerKpis {
  const valuations = rows
    .map((row) => row.valuation_usd)
    .filter((value): value is number => value != null && Number.isFinite(value));
  const caps = rows
    .map((row) => row.budget_cap_usd)
    .filter((value): value is number => value != null && Number.isFinite(value));
  const cpps = rows
    .filter((row) => row.points > 0 && row.cost_per_point != null)
    .map((row) => row.cost_per_point as number);

  const totalGridValuation = valuations.length ? valuations.reduce((sum, value) => sum + value, 0) : null;
  const avgCap = mean(caps);
  const avgCpp = mean(cpps);
  const capUtilization = avgCap != null ? avgCap / FIA_COST_CAP_USD : null;

  let inefficiency: number | null = null;
  if (avgCpp && cpps.length > 1) {
    const variance = cpps.reduce((sum, value) => sum + (value - avgCpp) ** 2, 0) / cpps.length;
    inefficiency = Math.sqrt(variance) / avgCpp;
  }

  const inefficiencyLabel: ManufacturerKpis["inefficiencyLabel"] =
    inefficiency == null ? "TIGHT" : inefficiency >= 0.45 ? "HIGH" : inefficiency >= 0.25 ? "ELEVATED" : "TIGHT";

  const efficient =
    rows
      .filter((row) => row.cost_per_point != null && row.points > 0)
      .slice()
      .sort((a, b) => (a.cost_per_point ?? Number.POSITIVE_INFINITY) - (b.cost_per_point ?? Number.POSITIVE_INFINITY))[0] ??
    null;

  const leader = rows.slice().sort((a, b) => a.position - b.position)[0] ?? null;
  const gridPoints = rows.reduce((sum, row) => sum + row.points, 0);
  const yieldShare = leader && gridPoints > 0 ? leader.points / gridPoints : null;

  return {
    totalGridValuation,
    avgCap,
    capUtilization,
    avgCpp,
    inefficiency,
    inefficiencyLabel,
    efficient,
    leader,
    yieldShare,
  };
}
