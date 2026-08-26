"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

import { ChatPanel } from "@/components/chat/ChatPanel";
import { DashboardView } from "@/components/dashboard/DashboardView";
import type { CommercialDeskTab } from "@/components/dashboard/ChampionshipTabs";
import { Skeleton } from "@/components/ui/skeleton";
import { formatApiError, loadDashboard } from "@/lib/api";
import type { DashboardPayload } from "@/lib/types";

type DashboardLoaderProps = {
  year: number;
  meetingKey?: number;
};

function resolveCommercialTab(raw: string | null): CommercialDeskTab {
  return raw === "driver" ? "driver" : "manufacturer";
}

function DashboardLoaderInner({ year, meetingKey }: DashboardLoaderProps) {
  const searchParams = useSearchParams();
  const activeTab = resolveCommercialTab(searchParams.get("tab"));
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
        <DashboardView data={data} error={error} activeTab={activeTab} showChat={false} />
      )}
      <ChatPanel year={year} meetingKey={meetingKey} />
    </div>
  );
}

export function DashboardLoader(props: DashboardLoaderProps) {
  return (
    <Suspense
      fallback={
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">Loading championship data…</p>
          <Skeleton className="h-10 w-64 bg-muted" />
          <Skeleton className="h-64 w-full bg-muted" />
        </div>
      }
    >
      <DashboardLoaderInner {...props} />
    </Suspense>
  );
}
