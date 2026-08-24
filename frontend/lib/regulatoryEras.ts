export type RegulatoryEraId = "turbo_hybrid" | "ground_effect" | "active_aero";

export type RegulatoryEra = {
  id: RegulatoryEraId;
  label: string;
  startYear: number;
  endYear: number;
  fill: string;
  summary: string;
};

export const REGULATORY_ERAS: RegulatoryEra[] = [
  {
    id: "turbo_hybrid",
    label: "Turbo-Hybrid",
    startYear: 2014,
    endYear: 2021,
    fill: "rgba(54, 113, 198, 0.10)",
    summary:
      "1.6L V6 turbo-hybrid with MGU-K and MGU-H. Token development limits early, then a freeze; the power unit became the dominant capital allocation problem on the grid.",
  },
  {
    id: "ground_effect",
    label: "Ground Effect",
    startYear: 2022,
    endYear: 2025,
    fill: "rgba(16, 185, 129, 0.10)",
    summary:
      "Ground-effect aero reset plus the FIA cost cap. Close racing was the sporting goal; the commercial goal was compressing the field’s ability to buy performance.",
  },
  {
    id: "active_aero",
    label: "Active Aero & 50/50 Power",
    startYear: 2026,
    endYear: 2030,
    fill: "rgba(225, 6, 0, 0.10)",
    summary:
      "Active aero replaces DRS, cars get lighter, and the MGU-H is removed. Power split moves toward ~50/50 ICE vs electrical — a new efficiency regime for constructor ROI.",
  },
];

export const YEAR_REGULATORY_NOTES: Record<number, string> = {
  2014: "Turbo-hybrid introduction: 1.6L V6, energy recovery, and a hard fuel-flow formula. Engine manufacturers became the scarce asset.",
  2017: "Wider cars and bigger tyres. Aerodynamic load jumped; tyre allocation and mechanical grip started to separate the field again.",
  2021: "Budget cap year one (~$145M then stepping down). Capital discipline became a sporting regulation, not just a finance policy.",
  2022: "Ground-effect regulations reset the aero order. Porpoising and floor development were the new R&D bottleneck.",
  2023: "Cost cap at the $135M class. Floor and water-cooling technical directives after the 2022 bounce.",
  2024: "Same ground-effect box, late-cycle development. Constructor yield now mostly reflects who allocated the cap to the right aero problems.",
  2025: "Final year of the ground-effect car. Development frozen toward 2026; residual performance is an asset-utilization story.",
  2026: "Active aero replaces DRS, lighter cars, MGU-H deleted, and a ~50/50 ICE/electric split. Treat 2026 points as a new accounting period, not a continuation.",
};

export function eraForYear(year: number): RegulatoryEra {
  return (
    REGULATORY_ERAS.find((era) => year >= era.startYear && year <= era.endYear) ??
    REGULATORY_ERAS[REGULATORY_ERAS.length - 1]
  );
}

export function whatChanged(year: number): { era: RegulatoryEra; note: string } {
  const era = eraForYear(year);
  return {
    era,
    note: YEAR_REGULATORY_NOTES[year] ?? `${era.label} era (${era.startYear}–${era.endYear}). ${era.summary}`,
  };
}
