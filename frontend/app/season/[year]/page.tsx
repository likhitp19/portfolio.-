import { DashboardLoader } from "@/components/dashboard/DashboardLoader";

type PageProps = {
  params: Promise<{ year: string }>;
};

export default async function SeasonPage({ params }: PageProps) {
  const { year: raw } = await params;
  return <DashboardLoader year={Number(raw)} />;
}
