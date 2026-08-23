import { DashboardLoader } from "@/components/dashboard/DashboardLoader";

type PageProps = {
  params: Promise<{ year: string; meetingKey: string }>;
};

export default async function MeetingPage({ params }: PageProps) {
  const { year: rawYear, meetingKey: rawMeeting } = await params;
  return <DashboardLoader year={Number(rawYear)} meetingKey={Number(rawMeeting)} />;
}
