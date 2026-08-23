import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DriverRoiGrid } from "@/components/dashboard/DriverCard";
import { ManufacturerStandings } from "@/components/dashboard/ManufacturerStandings";
import { OverallSummary } from "@/components/dashboard/OverallSummary";
import { PointsProgressionChart } from "@/components/dashboard/PointsProgressionChart";
import type {
  ChampionshipSummary,
  ConstructorStanding,
  DriverStanding,
  StandingsProgression,
} from "@/lib/types";

type ChampionshipTabsProps = {
  drivers: DriverStanding[];
  constructors: ConstructorStanding[];
  summary: ChampionshipSummary;
  driverProgression: StandingsProgression;
  constructorProgression?: StandingsProgression;
};

export function ChampionshipTabs({
  drivers,
  constructors,
  summary,
  driverProgression,
  constructorProgression,
}: ChampionshipTabsProps) {
  return (
    <Card>
      <CardContent className="pt-6">
        <Tabs defaultValue="manufacturer">
          <TabsList>
            <TabsTrigger value="manufacturer">Manufacturer</TabsTrigger>
            <TabsTrigger value="driver">Driver</TabsTrigger>
            <TabsTrigger value="summary">Overall Summary</TabsTrigger>
          </TabsList>
          <TabsContent value="manufacturer" className="space-y-4">
            <ManufacturerStandings rows={constructors} />
            <PointsProgressionChart
              data={constructorProgression?.series?.length ? constructorProgression : { circuits: [], series: [] }}
              title="Constructor championship over the season"
              subtitle="FIA constructor (manufacturer) points after each GP. Driver scores stay on the Driver tab."
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
      </CardContent>
    </Card>
  );
}
