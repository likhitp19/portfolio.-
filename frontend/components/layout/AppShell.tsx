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
      <main className="mx-auto min-h-[calc(100vh-3.5rem)] max-w-4xl px-4 py-6">{children}</main>
    </div>
  );
}
