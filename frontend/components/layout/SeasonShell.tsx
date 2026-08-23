"use client";

import { useEffect, useState, type ReactNode } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Alert } from "@/components/ui/alert";
import { fetchMeetings, fetchSeasons, formatApiError, F1_LIVE_LOCK } from "@/lib/api";
import type { Meeting } from "@/lib/types";

type SeasonShellProps = {
  year: number;
  children: ReactNode;
};

export function SeasonShell({ year, children }: SeasonShellProps) {
  const [years, setYears] = useState<number[]>([year]);
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [navError, setNavError] = useState<{ code?: string; message: string }>();

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchSeasons(), fetchMeetings(year)])
      .then(([seasons, nextMeetings]) => {
        if (cancelled) {
          return;
        }
        setYears(seasons.years.length ? seasons.years : [year]);
        setMeetings(nextMeetings);
        setNavError(undefined);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setNavError(formatApiError(err));
        }
      });
    return () => {
      cancelled = true;
    };
  }, [year]);

  return (
    <AppShell year={year} years={years} meetings={meetings}>
      {navError ? (
        <Alert variant="destructive">
          {navError.code ? (
            <p className="font-mono text-xs uppercase tracking-wide">Error {navError.code}</p>
          ) : null}
          <p className="mt-1">{navError.message}</p>
          {navError.code === F1_LIVE_LOCK ? (
            <p className="mt-2 text-muted-foreground">
              Historical data will work again after the session ends. Refresh the page then.
            </p>
          ) : null}
        </Alert>
      ) : null}
      {children}
    </AppShell>
  );
}
