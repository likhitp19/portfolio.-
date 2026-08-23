import { Badge } from "@/components/ui/badge";
import type { FactCitation } from "@/lib/types";

export function CitationHover({
  label,
  citation,
}: {
  label: string;
  citation?: FactCitation | null;
}) {
  const status = citation?.status ?? "defaulted";
  return (
    <span className="group relative inline-flex">
      <Badge className="cursor-default">{label}</Badge>
      <span className="pointer-events-none absolute left-0 top-full z-30 mt-1 hidden w-64 rounded-md border border-border bg-card p-2 text-xs text-foreground shadow-lg group-hover:block">
        <p className="font-medium capitalize">{status}</p>
        {citation?.source_title ? <p className="mt-1">{citation.source_title}</p> : null}
        {citation?.source_url ? <p className="mt-1 break-all text-muted-foreground">{citation.source_url}</p> : null}
        {citation?.retrieved_at ? <p className="mt-1 text-muted-foreground">{citation.retrieved_at}</p> : null}
        {citation?.snippet ? <p className="mt-1 text-muted-foreground">{citation.snippet}</p> : null}
      </span>
    </span>
  );
}
