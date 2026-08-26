"use client";

import { useParams, useRouter } from "next/navigation";

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
    <div className="border-b border-[#2A2A2A] bg-[#121212]/90">
      <div className="mx-auto flex h-12 max-w-7xl items-center justify-between gap-4 px-6">
        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Season controls
        </p>
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
    </div>
  );
}
