import type { ReactNode } from "react";

import { SeasonShell } from "@/components/layout/SeasonShell";

type LayoutProps = {
  children: ReactNode;
  params: Promise<{ year: string }>;
};

export default async function SeasonLayout({ children, params }: LayoutProps) {
  const { year: raw } = await params;
  return <SeasonShell year={Number(raw)}>{children}</SeasonShell>;
}
