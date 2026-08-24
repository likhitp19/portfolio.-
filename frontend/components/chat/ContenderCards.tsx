"use client";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Card, CardContent } from "@/components/ui/card";
import type { DriverContender } from "@/lib/types";

function initials(name: string) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

export function ContenderCards({ contenders }: { contenders: DriverContender[] }) {
  if (!contenders.length) {
    return null;
  }
  return (
    <div>
      <p className="mb-3 text-[10px] font-medium uppercase tracking-[0.16em] text-muted-foreground">Key Contenders</p>
      <div className="grid gap-3 sm:grid-cols-2">
        {contenders.map((driver) => (
          <Card key={driver.driver_number || driver.full_name} className="rounded-2xl border-[#2A2A2A] bg-[#0A0A0A]">
            <CardContent className="flex items-center gap-3 p-4">
              <Avatar className="h-14 w-14 ring-1 ring-[#2A2A2A]">
                {driver.headshot_url ? (
                  <AvatarImage src={driver.headshot_url} alt={driver.full_name} />
                ) : (
                  <AvatarFallback>{initials(driver.full_name) || driver.driver_number}</AvatarFallback>
                )}
              </Avatar>
              <div className="min-w-0">
                <p className="truncate font-semibold tracking-tight">{driver.full_name}</p>
                <p className="text-xs text-muted-foreground">{driver.team_name}</p>
                <p className="mt-1 font-mono text-[11px] text-[#10B981]">
                  P{driver.position} · {Math.round(driver.points)} pts
                </p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
