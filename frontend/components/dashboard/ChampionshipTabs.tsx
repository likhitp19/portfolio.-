import { ConstructorEraTimeline } from "@/components/dashboard/ConstructorEraTimeline";
import { DriverRoiGrid } from "@/components/dashboard/DriverCard";
import { ManufacturerDashboard } from "@/components/dashboard/ManufacturerDashboard";
import { PointsProgressionChart } from "@/components/dashboard/PointsProgressionChart";
import { TeammateDeltaMatrix } from "@/components/dashboard/TeammateDeltaMatrix";
import type {
  ConstructorStanding,
  DriverStanding,
  StandingsProgression,
} from "@/lib/types";

export type CommercialDeskTab = "manufacturer" | "driver";

type ChampionshipTabsProps = {
  year: number;
  activeTab: CommercialDeskTab;
  drivers: DriverStanding[];
  constructors: ConstructorStanding[];
  driverProgression: StandingsProgression;
  constructorProgression?: StandingsProgression;
};

export function ChampionshipTabs({
  year,
  activeTab,
  drivers,
  constructors,
  driverProgression,
  constructorProgression,
}: ChampionshipTabsProps) {
  if (activeTab === "driver") {
    return (
      <div className="space-y-4">
        <DriverRoiGrid rows={drivers} />
        <TeammateDeltaMatrix year={year} />
        <PointsProgressionChart
          data={driverProgression}
          title="Driver title chase"
          subtitle="Top five retainers as a championship burn-down, circuit by circuit."
        />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <ManufacturerDashboard rows={constructors} year={year} />
      <ConstructorEraTimeline />
      <PointsProgressionChart
        data={constructorProgression?.series?.length ? constructorProgression : { circuits: [], series: [] }}
        title="Constructor yield over the season"
        subtitle="FIA constructor points after each GP. Driver scores stay on Driver Assets."
      />
    </div>
  );
}
