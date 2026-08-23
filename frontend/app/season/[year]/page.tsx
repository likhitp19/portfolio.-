import { DashboardView } from "@/components/dashboard/DashboardView";
import { formatApiError, loadDashboard } from "@/lib/api";

type PageProps = {
  params: Promise<{ year: string }>;
};

export default async function SeasonPage({ params }: PageProps) {
  const { year: raw } = await params;
  const year = Number(raw);
  try {
    const data = await loadDashboard(year);
    return <DashboardView data={data} />;
  } catch (error) {
    return <DashboardView error={formatApiError(error)} />;
  }
}
