import type { ReactNode } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Alert } from "@/components/ui/alert";
import { fetchMeetings, fetchSeasons, formatApiError, F1_LIVE_LOCK } from "@/lib/api";

type LayoutProps = {
  children: ReactNode;
  params: Promise<{ year: string }>;
};

export default async function SeasonLayout({ children, params }: LayoutProps) {
  const { year: raw } = await params;
  const year = Number(raw);
  try {
    const [seasons, meetings] = await Promise.all([fetchSeasons(), fetchMeetings(year)]);
    return (
      <AppShell year={year} years={seasons.years} meetings={meetings}>
        {children}
      </AppShell>
    );
  } catch (error) {
    const { code, message } = formatApiError(error);
    return (
      <AppShell year={year} years={[year]} meetings={[]}>
        <Alert variant="destructive">
          {code ? <p className="font-mono text-xs uppercase tracking-wide">Error {code}</p> : null}
          <p className="mt-1">{message}</p>
          {code === F1_LIVE_LOCK ? (
            <p className="mt-2 text-muted-foreground">
              Historical data will work again after the session ends. Refresh the page then.
            </p>
          ) : null}
        </Alert>
        {children}
      </AppShell>
    );
  }
}
