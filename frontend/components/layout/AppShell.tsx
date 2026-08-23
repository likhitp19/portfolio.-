import type { ReactNode } from "react";

import { TopNav } from "@/components/layout/TopNav";
import type { Meeting } from "@/lib/types";

type AppShellProps = {
  year: number;
  years: number[];
  meetings: Meeting[];
  meetingKey?: number;
  children: ReactNode;
};

export function AppShell({ year, years, meetings, meetingKey, children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <TopNav year={year} years={years} meetings={meetings} meetingKey={meetingKey} />
      <main className="mx-auto grid max-w-7xl gap-6 px-6 py-8">{children}</main>
    </div>
  );
}
