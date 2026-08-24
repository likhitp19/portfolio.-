"use client";

import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Collapsible({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDetailsElement>) {
  return (
    <details className={cn("group border border-[#2A2A2A] bg-[#0A0A0A]", className)} {...props}>
      {children}
    </details>
  );
}

export function CollapsibleTrigger({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLElement>) {
  return (
    <summary
      className={cn(
        "cursor-pointer list-none px-3 py-2 text-[10px] font-medium uppercase tracking-[0.16em] text-muted-foreground marker:hidden [&::-webkit-details-marker]:hidden",
        className,
      )}
      {...props}
    >
      {children}
    </summary>
  );
}

export function CollapsibleContent({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("border-t border-[#2A2A2A] px-3 py-3", className)} {...props} />;
}
