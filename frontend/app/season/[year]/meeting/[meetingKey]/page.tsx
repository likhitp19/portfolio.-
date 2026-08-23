import { DashboardView } from "@/components/dashboard/DashboardView";
import { formatApiError, loadDashboard } from "@/lib/api";

type PageProps = {
  params: Promise<{ year: string; meetingKey: string }>;
};

export default async function MeetingPage({ params }: PageProps) {
  const { year: rawYear, meetingKey: rawMeeting } = await params;
  const year = Number(rawYear);
  const meetingKey = Number(rawMeeting);
  try {
    const data = await loadDashboard(year, meetingKey);
    return <DashboardView data={data} />;
  } catch (error) {
    return <DashboardView error={formatApiError(error)} />;
  }
}
