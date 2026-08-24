import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DriverRoiGrid } from "@/components/dashboard/DriverCard";
import { ManufacturerDashboard } from "@/components/dashboard/ManufacturerDashboard";
import { OverallSummary } from "@/components/dashboard/OverallSummary";
import { PointsProgressionChart } from "@/components/dashboard/PointsProgressionChart";
import type {
  ChampionshipSummary,
  ConstructorStanding,
  DriverStanding,
  StandingsProgression,
} from "@/lib/types";

type ChampionshipTabsProps = {
  year: number;
  drivers: DriverStanding[];
  constructors: ConstructorStanding[];
  summary: ChampionshipSummary;
  driverProgression: StandingsProgression;
  constructorProgression?: StandingsProgression;
};

export function ChampionshipTabs({
  year,
  drivers,
  constructors,
  summary,
  driverProgression,
  constructorProgression,
}: ChampionshipTabsProps) {
  return (
    <Tabs defaultValue="manufacturer">
      <TabsList className="h-auto rounded-sm border border-[#2A2A2A] bg-[#1A1A1A] p-0">
        <TabsTrigger
          className="rounded-none px-4 py-2 text-xs uppercase tracking-[0.16em] data-[state=active]:bg-[#2A2A2A] data-[state=active]:text-[#E10600] data-[state=active]:shadow-none"
          value="manufacturer"
        >
          Manufacturer ROI
        </TabsTrigger>
        <TabsTrigger
          className="rounded-none px-4 py-2 text-xs uppercase tracking-[0.16em] data-[state=active]:bg-[#2A2A2A] data-[state=active]:text-[#E10600] data-[state=active]:shadow-none"
          value="driver"
        >
          Driver Assets
        </TabsTrigger>
        <TabsTrigger
          className="rounded-none px-4 py-2 text-xs uppercase tracking-[0.16em] data-[state=active]:bg-[#2A2A2A] data-[state=active]:text-[#E10600] data-[state=active]:shadow-none"
          value="summary"
        >
          Market Book
        </TabsTrigger>
      </TabsList>
      <TabsContent value="manufacturer" className="space-y-4">
        <ManufacturerDashboard rows={constructors} year={year} />
        <PointsProgressionChart
          data={constructorProgression?.series?.length ? constructorProgression : { circuits: [], series: [] }}
          title="Constructor yield over the season"
          subtitle="FIA constructor points after each GP. Driver scores stay on Driver Assets."
        />
      </TabsContent>
      <TabsContent value="driver" className="space-y-4">
        <DriverRoiGrid rows={drivers} />
        <PointsProgressionChart
          data={driverProgression}
          title="Driver title chase"
          subtitle="Top five retainers as a championship burn-down, circuit by circuit."
        />
      </TabsContent>
      <TabsContent value="summary">
        <OverallSummary summary={summary} constructors={constructors} />
      </TabsContent>
    </Tabs>
  );
}
