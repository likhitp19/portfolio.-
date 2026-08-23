import { Skeleton } from "@/components/ui/skeleton";

export default function Loading() {
  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">Loading circuit weekend…</p>
      <Skeleton className="h-10 w-64 bg-muted" />
      <Skeleton className="h-64 w-full bg-muted" />
    </div>
  );
}
