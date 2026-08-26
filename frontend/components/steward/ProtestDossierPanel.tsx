"use client";

import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import type { EvidenceStatus, ProtestDossier, SuccessProbability } from "@/lib/steward";

const STATUS_STYLES: Record<EvidenceStatus, string> = {
  present: "border-[#10B981] bg-[#10B981]/15 text-[#10B981]",
  pending_phase2: "border-[#C8A24A] bg-[#C8A24A]/15 text-[#C8A24A]",
  insufficient: "border-[#E10600] bg-[#E10600]/10 text-[#E10600]",
};

const STATUS_LABEL: Record<EvidenceStatus, string> = {
  present: "Present",
  pending_phase2: "Pending Phase 2",
  insufficient: "Insufficient",
};

const PROBABILITY_META: Record<
  SuccessProbability,
  { pct: number; bar: string; text: string; label: string }
> = {
  Low: { pct: 28, bar: "bg-[#E10600]", text: "text-[#E10600]", label: "Low" },
  Medium: { pct: 58, bar: "bg-[#C8A24A]", text: "text-[#C8A24A]", label: "Medium" },
  High: { pct: 86, bar: "bg-[#10B981]", text: "text-[#10B981]", label: "High" },
};

export function ProtestDossierPanel({
  dossier,
  disclaimer,
}: {
  dossier: ProtestDossier | null;
  disclaimer?: string;
}) {
  if (!dossier) {
    return (
      <article className="overflow-hidden rounded-sm border border-[#C8A24A]/35 bg-[#111111]">
        <DossierHeader />
        <div className="px-6 py-8 text-sm text-muted-foreground">
          Phase 1 produces a formal Mercedes-AMG Petronas FIA Protest Dossier once assessment completes.
        </div>
      </article>
    );
  }

  const probability = PROBABILITY_META[dossier.success_probability] ?? PROBABILITY_META.Low;
  const filingLabel =
    dossier.filing_type === "right_of_review" ? "Article 14 — Right of Review" : "Article 13 — Protest";

  return (
    <article className="overflow-hidden rounded-sm border border-[#C8A24A]/40 bg-[#0D0D0D] shadow-[0_0_0_1px_rgba(200,162,74,0.08)]">
      <DossierHeader filingLabel={filingLabel} />

      <div className="grid gap-6 px-6 py-6 text-sm">
        {disclaimer ? (
          <p className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{disclaimer}</p>
        ) : null}

        <section className="grid gap-3">
          <SectionTitle>Filing particulars</SectionTitle>
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="Filing team" value={dossier.filing_team} />
            <Field label="Competitor" value={dossier.competitor_team || "—"} />
          </div>
          <Field label="Primary claim" value={dossier.primary_claim} />
        </section>

        <Separator className="bg-[#2A2A2A]" />

        <section className="grid gap-3">
          <SectionTitle>Success probability</SectionTitle>
          <div className="flex items-end justify-between gap-3">
            <p className={`font-[family-name:var(--font-geist-mono),ui-monospace,monospace] text-2xl font-semibold tracking-tight ${probability.text}`}>
              {probability.label}
            </p>
            <Badge className={`rounded-sm border bg-transparent ${probability.text} border-current`}>
              Phase 1 assessment
            </Badge>
          </div>
          <Progress value={probability.pct} indicatorClassName={probability.bar} className="h-2.5" />
          <p className="text-xs text-muted-foreground">
            Probability remains Low while micro-telemetry items are pending Phase 2 ingestion.
          </p>
        </section>

        <Separator className="bg-[#2A2A2A]" />

        <section className="grid gap-3">
          <SectionTitle>Regulatory violations</SectionTitle>
          {(dossier.regulatory_violations || []).length === 0 ? (
            <p className="text-muted-foreground">No citations returned.</p>
          ) : (
            <div className="grid gap-4">
              {dossier.regulatory_violations.map((cite, index) => (
                <div
                  key={`${cite.article_name}-${cite.page_number}-${index}`}
                  className="border border-[#2A2A2A] bg-[#121212] p-4"
                >
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <h3 className="font-[family-name:var(--font-geist-mono),ui-monospace,monospace] text-[13px] font-semibold tracking-wide text-[#F5F5F5]">
                      {cite.article_name || "Unnamed article"}
                    </h3>
                    <Badge className="rounded-sm border border-[#C8A24A]/50 bg-[#C8A24A]/10 text-[10px] uppercase tracking-[0.12em] text-[#C8A24A]">
                      {cite.source_document || "source unknown"}
                      {cite.page_number > 0 ? ` · p.${cite.page_number}` : " · p.—"}
                    </Badge>
                  </div>
                  <blockquote className="mt-3 border-l-2 border-[#C8A24A] bg-[#0A0A0A] py-3 pl-4 pr-3 text-[13px] leading-relaxed text-[#D4D4D4]">
                    <span className="mr-1 text-[#C8A24A]">“</span>
                    {cite.exact_quote || "—"}
                    <span className="ml-1 text-[#C8A24A]">”</span>
                  </blockquote>
                </div>
              ))}
            </div>
          )}
        </section>

        <Separator className="bg-[#2A2A2A]" />

        <section className="grid gap-3">
          <SectionTitle>Evidence checklist</SectionTitle>
          <Field label="Available evidence" value={dossier.available_evidence_summary} />
          <div className="grid gap-2">
            {(dossier.required_telemetry_evidence || []).map((item) => (
              <div key={item.id} className="border border-[#2A2A2A] bg-[#121212] p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-medium text-[#F5F5F5]">{item.label}</p>
                  <Badge className={`rounded-sm border text-[10px] uppercase tracking-[0.14em] ${STATUS_STYLES[item.status]}`}>
                    {STATUS_LABEL[item.status]}
                  </Badge>
                </div>
                <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{item.rationale}</p>
                {item.phase2_schema_ref ? (
                  <p className="mt-1.5 font-mono text-[11px] text-[#C8A24A]">schema: {item.phase2_schema_ref}</p>
                ) : null}
              </div>
            ))}
          </div>
        </section>

        <Separator className="bg-[#2A2A2A]" />

        <section className="grid gap-3">
          <SectionTitle>Counsel notes</SectionTitle>
          <Field label="Legal risk" value={dossier.legal_risk_notes} />
          <Field label="Recommended next step" value={dossier.recommended_next_step} />
          <p className="border-t border-[#2A2A2A] pt-3 text-xs leading-relaxed text-muted-foreground">
            {dossier.phase2_bridge}
          </p>
        </section>
      </div>
    </article>
  );
}

function DossierHeader({ filingLabel }: { filingLabel?: string }) {
  return (
    <header className="relative overflow-hidden border-b border-[#C8A24A]/30 bg-[#141414] px-6 py-5">
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.07]"
        style={{
          backgroundImage:
            "repeating-linear-gradient(90deg, #C8A24A 0 1px, transparent 1px 48px), repeating-linear-gradient(0deg, #C8A24A 0 1px, transparent 1px 48px)",
        }}
      />
      <div className="relative flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[#C8A24A]">
            Mercedes-AMG Petronas Formula One Team
          </p>
          <h2 className="mt-2 font-[family-name:var(--font-geist-mono),ui-monospace,monospace] text-lg font-bold tracking-[0.04em] text-[#FAFAFA] sm:text-xl">
            FIA Protest Dossier
          </h2>
          <p className="mt-1 text-xs uppercase tracking-[0.16em] text-muted-foreground">
            Phase 1 — Legal assessment & evidence bridge
          </p>
        </div>
        {filingLabel ? (
          <Badge className="rounded-sm border border-[#E10600]/60 bg-[#E10600]/10 text-[10px] uppercase tracking-[0.14em] text-[#E10600]">
            {filingLabel}
          </Badge>
        ) : null}
      </div>
    </header>
  );
}

function SectionTitle({ children }: { children: ReactNode }) {
  return (
    <h3 className="text-[10px] font-semibold uppercase tracking-[0.22em] text-[#C8A24A]">{children}</h3>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">{label}</p>
      <p className="mt-1 leading-relaxed text-[#E5E5E5]">{value || "—"}</p>
    </div>
  );
}
