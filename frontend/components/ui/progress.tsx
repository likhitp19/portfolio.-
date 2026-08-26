import * as React from "react";

import { cn } from "@/lib/utils";

type ProgressProps = React.HTMLAttributes<HTMLDivElement> & {
  value?: number;
  indicatorClassName?: string;
};

export function Progress({ className, value = 0, indicatorClassName, ...props }: ProgressProps) {
  const clamped = Math.max(0, Math.min(100, Number.isFinite(value) ? value : 0));
  return (
    <div
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(clamped)}
      className={cn("relative h-2 w-full overflow-hidden rounded-sm bg-[#2A2A2A]", className)}
      {...props}
    >
      <div
        className={cn("h-full transition-[width] duration-500 ease-out", indicatorClassName)}
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
