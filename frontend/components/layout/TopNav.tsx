"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import type { Meeting } from "@/lib/types";

type TopNavProps = {
  year: number;
  years: number[];
  meetings: Meeting[];
  meetingKey?: number;
};

export function TopNav({ year, years, meetings, meetingKey }: TopNavProps) {
  const router = useRouter();
  const params = useParams<{ year?: string; meetingKey?: string }>();
  const selectedYear = Number(params.year || year);
  const selectedMeeting = params.meetingKey ? Number(params.meetingKey) : meetingKey;
  const seasonYears = years.length ? years : [selectedYear];

  return (
    <header className="border-b border-[color:var(--gold)]/15 bg-black/40 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-3">
          <Link href={`/season/${selectedYear}`} className="font-serif text-xl tracking-tight">
            Paddock Ledger
          </Link>
          <Badge className="border-[color:var(--gold)]/30 bg-transparent text-[10px] uppercase tracking-[0.16em] text-[color:var(--gold)]">
            Commercial
          </Badge>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <label className="text-xs uppercase tracking-wide text-muted-foreground">
            Season
            <select
              className="ml-2 h-9 rounded-md border border-input bg-card px-2 text-sm text-foreground"
              style={{ colorScheme: "dark" }}
              value={selectedYear}
              onChange={(event) => router.push(`/season/${event.target.value}`)}
            >
              {seasonYears.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
          <label className="text-xs uppercase tracking-wide text-muted-foreground">
            Circuit
            <select
              className="ml-2 h-9 max-w-64 rounded-md border border-input bg-card px-2 text-sm text-foreground"
              style={{ colorScheme: "dark" }}
              value={selectedMeeting ?? ""}
              onChange={(event) => {
                const value = event.target.value;
                if (!value) {
                  router.push(`/season/${selectedYear}`);
                  return;
                }
                router.push(`/season/${selectedYear}/meeting/${value}`);
              }}
            >
              <option value="">All Circuits</option>
              {meetings.map((meeting) => (
                <option key={meeting.meeting_key} value={meeting.meeting_key}>
                  {meeting.circuit_short_name || meeting.meeting_name}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>
    </header>
  );
}
