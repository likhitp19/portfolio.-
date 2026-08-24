"use client";

import { ChatPanel } from "@/components/chat/ChatPanel";

type DashboardLoaderProps = {
  year: number;
  meetingKey?: number;
};

export function DashboardLoader({ year, meetingKey }: DashboardLoaderProps) {
  return <ChatPanel year={year} meetingKey={meetingKey} />;
}
