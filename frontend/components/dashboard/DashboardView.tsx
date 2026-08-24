import { ChampionshipTabs } from "@/components/dashboard/ChampionshipTabs";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { Alert } from "@/components/ui/alert";
import { F1_LIVE_LOCK } from "@/lib/api";
import type { DashboardPayload } from "@/lib/types";

export function DashboardView({
  data,
  error,
  showChat = true,
}: {
  data?: DashboardPayload;
  error?: { code?: string; message: string };
  showChat?: boolean;
}) {
  if (error || !data) {
    const code = error?.code;
    const liveLock = code === F1_LIVE_LOCK;
    return (
      <Alert variant="destructive">
        {code ? (
          <p className="font-mono text-xs uppercase tracking-wide">
            Error {code}
          </p>
        ) : null}
        <p className="mt-1">
          {error?.message ?? "Dashboard data is unavailable."}
        </p>
        {liveLock ? (
          <p className="mt-2 text-muted-foreground">
            Historical data will work again after the session ends. Refresh the page then.
          </p>
        ) : null}
      </Alert>
    );
  }

  const meeting = data.meetingKey
    ? data.meetings.find((item) => item.meeting_key === data.meetingKey)
    : undefined;
  const viewKey = `${data.year}-${data.meetingKey ?? "all"}`;

  return (
    <>
      <div>
        <p className="text-[10px] font-medium uppercase tracking-[0.28em] text-[#E10600]">Apex Analytics · Championship book</p>
        <h1 className="text-3xl font-bold tracking-tight">
          {meeting ? meeting.meeting_name : `${data.year} season ledger`}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {meeting
            ? `${meeting.circuit_short_name} · ${meeting.country_name}`
            : "Constructor yield, cost per point, and asset expenditure — one meeting_key, one payload."}
        </p>
      </div>
      <ChampionshipTabs
        key={`tabs-${viewKey}`}
        year={data.year}
        drivers={data.drivers}
        constructors={data.constructors}
        summary={data.summary}
        driverProgression={data.progression}
        constructorProgression={data.constructor_progression}
      />
      {showChat ? <ChatPanel year={data.year} meetingKey={data.meetingKey} /> : null}
    </>
  );
}
