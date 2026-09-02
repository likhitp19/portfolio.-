import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import type { RoadmapItem } from "@/lib/portfolio/types";

const STATUS_LABEL: Record<RoadmapItem["status"], string> = {
  planned: "Planned",
  "in-design": "In design",
  "contract-ready": "Contract ready",
};

const STATUS_COLOR: Record<RoadmapItem["status"], string> = {
  planned: "border-[#2A2A2A] text-muted-foreground",
  "in-design": "border-[#C8A24A]/40 text-[#C8A24A]",
  "contract-ready": "border-[#10B981]/40 text-[#10B981]",
};

export function Phase4Roadmap({ items }: { items: RoadmapItem[] }) {
  return (
    <section className="space-y-6" aria-labelledby="phase4-heading">
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-[#C8A24A]">Phase 4 architectural roadmap</p>
        <h2 id="phase4-heading" className="mt-2 font-serif text-2xl font-semibold text-[#FAFAFA]">
          Scale-ready expansion — not backlog debt
        </h2>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
          Advanced sporting analytics and high-frequency telemetry are modeled as the next architecture phase — with eval
          catalog entries, API contracts, and dossier evidence slots already reserved.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {items.map((item) => (
          <Card key={item.id} className="border-[#2A2A2A] bg-[#111111] shadow-none">
            <CardContent className="p-6">
              <div className="mb-3 flex items-start justify-between gap-3">
                <h3 className="text-base font-semibold text-[#FAFAFA]">{item.title}</h3>
                <Badge className={`shrink-0 rounded-sm bg-transparent text-[10px] uppercase ${STATUS_COLOR[item.status]}`}>
                  {STATUS_LABEL[item.status]}
                </Badge>
              </div>
              <p className="text-sm leading-relaxed text-muted-foreground">{item.summary}</p>
              <ul className="mt-4 space-y-2 text-sm text-foreground/80">
                {item.unlocks.map((unlock) => (
                  <li key={unlock} className="flex gap-2">
                    <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-[#E10600]" aria-hidden />
                    <span>{unlock}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
}
