import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export function Avatar({
  className,
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return (
    <span className={cn("relative flex h-16 w-16 shrink-0 overflow-hidden rounded-full bg-[#1A1A1A]", className)}>
      {children}
    </span>
  );
}

export function AvatarImage({ src, alt }: { src?: string | null; alt: string }) {
  if (!src) {
    return null;
  }
  return (
    // Official OpenF1 / Formula 1 media headshots (headshot_url).
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt={alt} className="h-full w-full object-cover object-top" />
  );
}

export function AvatarFallback({ children }: { children: ReactNode }) {
  return (
    <span className="flex h-full w-full items-center justify-center font-mono text-sm text-muted-foreground">
      {children}
    </span>
  );
}
