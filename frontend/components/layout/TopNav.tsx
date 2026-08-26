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
  const seasonYears = Array.from(new Set([...years, 2026, selectedYear])).sort((a, b) => b - a);

  return (
    <header className="sticky top-0 z-50 border-b border-[#2A2A2A] bg-[#1A1A1A]">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between gap-4 px-6">
        <div className="flex min-w-0 items-center gap-6">
          <Link href="/season/2026" className="shrink-0 text-lg font-black tracking-tighter text-[#E10600]">
            APEX ANALYTICS
          </Link>
          <Link
            href="/steward"
            className="hidden text-[10px] font-medium uppercase tracking-[0.16em] text-muted-foreground hover:text-foreground sm:inline"
          >
            Protest Engine
          </Link>
          <Badge className="hidden rounded-sm border-[#2A2A2A] bg-transparent text-[10px] uppercase tracking-[0.16em] text-muted-foreground sm:inline-flex">
            Executive Pitwall
          </Badge>
        </div>
        <div className="flex flex-wrap items-center justify-end gap-3">
          <label className="text-[10px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
            Season
            <select
              className="ml-2 h-8 rounded-sm border border-[#2A2A2A] bg-[#0A0A0A] px-2 text-sm text-foreground"
              style={{ colorScheme: "dark" }}
              value={selectedYear === 2025 ? 2026 : selectedYear}
              onChange={(event) => router.push(`/season/${event.target.value}`)}
            >
              {seasonYears.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
          <label className="text-[10px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
            All Circuits
            <select
              className="ml-2 h-8 max-w-64 rounded-sm border border-[#2A2A2A] bg-[#0A0A0A] px-2 text-sm text-foreground"
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
