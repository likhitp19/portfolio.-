"use client";

import { useEffect, useState } from "react";

import { ChatPanel } from "@/components/chat/ChatPanel";
import { DashboardView } from "@/components/dashboard/DashboardView";
import { Skeleton } from "@/components/ui/skeleton";
import { formatApiError, loadDashboard } from "@/lib/api";
import type { DashboardPayload } from "@/lib/types";

type DashboardLoaderProps = {
  year: number;
  meetingKey?: number;
};

export function DashboardLoader({ year, meetingKey }: DashboardLoaderProps) {
  const [data, setData] = useState<DashboardPayload>();
  const [error, setError] = useState<{ code?: string; message: string }>();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(undefined);
    loadDashboard(year, meetingKey)
      .then((payload) => {
        if (!cancelled) {
          setData(payload);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setData(undefined);
          setError(formatApiError(err));
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [year, meetingKey]);

  return (
    <div className="space-y-10">
      {loading ? (
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">Loading championship data…</p>
          <Skeleton className="h-10 w-64 bg-muted" />
          <Skeleton className="h-64 w-full bg-muted" />
        </div>
      ) : (
        <DashboardView data={data} error={error} showChat={false} />
      )}
      <ChatPanel year={year} meetingKey={meetingKey} />
    </div>
  );
}
