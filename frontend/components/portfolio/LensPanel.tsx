import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import type { LensId, ProjectLensContent } from "@/lib/portfolio/types";
import { cn } from "@/lib/utils";

const VARIANT_STYLES: Record<LensId, { accent: string; badge: string }> = {
  business: {
    accent: "border-[#10B981]/30",
    badge: "border-[#10B981]/40 text-[#10B981]",
  },
  technical: {
    accent: "border-[#C8A24A]/30",
    badge: "border-[#C8A24A]/40 text-[#C8A24A]",
  },
};

export function LensPanel({ content, variant }: { content: ProjectLensContent; variant: LensId }) {
  const styles = VARIANT_STYLES[variant];

  return (
    <article className={cn("rounded-sm border bg-[#111111] p-6 sm:p-8", styles.accent)}>
      <Badge className={cn("mb-4 rounded-sm bg-transparent text-[10px] uppercase tracking-[0.18em]", styles.badge)}>
        {variant === "business" ? "Business impact" : "System architecture"}
      </Badge>
      <h2 className="font-serif text-2xl font-semibold tracking-tight text-[#FAFAFA]">{content.headline}</h2>
      <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{content.intro}</p>

      <div className="mt-8 space-y-8">
        {content.sections.map((section) => (
          <section key={section.id} className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-[0.2em] text-[#E10600]">{section.title}</h3>
            <p className="text-sm leading-relaxed text-foreground/90">{section.body}</p>
            {section.bullets?.length ? (
              <ul className="space-y-2 text-sm text-muted-foreground">
                {section.bullets.map((bullet) => (
                  <li key={bullet} className="flex gap-2">
                    <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-[#E10600]" aria-hidden />
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>
            ) : null}
            {section.metrics?.length ? (
              <div className="grid gap-3 sm:grid-cols-2">
                {section.metrics.map((metric) => (
                  <Card key={metric.label} className="border-[#2A2A2A] bg-[#0A0A0A] shadow-none">
                    <CardContent className="p-4">
                      <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">{metric.label}</p>
                      <p className="mt-1 font-mono text-lg font-semibold text-[#FAFAFA]">{metric.value}</p>
                      {metric.hint ? <p className="mt-1 text-xs text-muted-foreground">{metric.hint}</p> : null}
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : null}
          </section>
        ))}
      </div>
    </article>
  );
}
