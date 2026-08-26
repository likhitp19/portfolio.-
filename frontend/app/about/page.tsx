import type { Metadata } from "next";
import Image from "next/image";
import { BrainCircuit, Database, Mail, Phone, Radar } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

export const metadata: Metadata = {
  title: "About — Apex F1 Suite",
  description: "Likhit P. — Senior AI Product / Systems Engineer.",
};

const PROFILE = {
  name: "Likhit P.",
  title: "Senior AI Product / Systems Engineer",
  tagline:
    "Bridging complex agentic AI systems, multimodal vision pipelines, and scalable technical product architectures.",
  email: "likhit.p19@gmail.com",
  phone: "+918123856002",
} as const;

const LIFE_PHOTOS = [
  {
    title: "Sunset on the water",
    image: "/images/sunset.jpg",
  },
  {
    title: "Northern lights",
    image: "/images/aurora.png",
  },
] as const;

const STACK_PILLARS = [
  {
    icon: BrainCircuit,
    title: "Agentic Workflows",
    badge: "LangGraph",
    description: "LangGraph-driven routing, tool orchestration, and resilient fallback systems.",
  },
  {
    icon: Database,
    title: "Domain-Specific RAG",
    badge: "Pinecone",
    description: "Legal vector search with strict chunk metadata — citations traceable to source and page.",
  },
  {
    icon: Radar,
    title: "Multimodal Telemetry",
    badge: "OpenF1 + Qwen-VL",
    description: "Vision plus time-series data to ground regulatory reasoning in on-track evidence.",
  },
] as const;

export default function AboutPage() {
  return (
    <main className="mx-auto max-w-7xl px-6 py-10 lg:py-16">
      <section className="grid gap-10 lg:grid-cols-[minmax(0,280px)_1fr] lg:items-center lg:gap-16">
        <div className="mx-auto w-full max-w-[280px] lg:mx-0">
          <div className="rounded-full bg-gradient-to-br from-[#E10600] via-[#C8A24A] to-[#10B981] p-[3px] shadow-[0_0_40px_rgba(225,6,0,0.15)]">
            <div className="overflow-hidden rounded-full bg-[#0E0E0E] p-1">
              <div className="relative aspect-square overflow-hidden rounded-full">
                <Image
                  src="/images/profile.jpg"
                  alt={`${PROFILE.name} profile`}
                  fill
                  priority
                  className="object-cover"
                  sizes="280px"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-6 text-center lg:text-left">
          <div className="space-y-3">
            <h1 className="font-[family-name:var(--font-fraunces),ui-serif,Georgia,serif] text-4xl font-semibold tracking-tight text-[#FAFAFA] sm:text-5xl">
              {PROFILE.name}
            </h1>
            <p className="text-lg font-medium text-[#E10600] sm:text-xl">{PROFILE.title}</p>
          </div>

          <p className="mx-auto max-w-2xl text-base leading-relaxed text-muted-foreground lg:mx-0 lg:text-lg">
            {PROFILE.tagline}
          </p>

          <div className="flex flex-wrap items-center justify-center gap-2 lg:justify-start">
            <Button asChild variant="outline" size="sm" className="border-[#2A2A2A] bg-[#121212] hover:bg-[#1A1A1A]">
              <a href={`mailto:${PROFILE.email}`}>
                <Mail className="h-4 w-4" />
                {PROFILE.email}
              </a>
            </Button>
            <Button asChild variant="outline" size="sm" className="border-[#2A2A2A] bg-[#121212] hover:bg-[#1A1A1A]">
              <a href={`tel:${PROFILE.phone}`}>
                <Phone className="h-4 w-4" />
                {PROFILE.phone}
              </a>
            </Button>
          </div>
        </div>
      </section>

      <section className="space-y-4 pt-4">
        <h2 className="font-[family-name:var(--font-fraunces),ui-serif,Georgia,serif] text-2xl font-semibold tracking-tight sm:text-3xl">
          Life outside work
        </h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {LIFE_PHOTOS.map((photo) => (
            <figure
              key={photo.title}
              className="overflow-hidden rounded-sm border border-[#2A2A2A] bg-[#121212]"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={photo.image} alt={photo.title} className="block h-auto min-h-[220px] w-full object-cover" />
              <figcaption className="px-4 py-3 text-sm text-muted-foreground">{photo.title}</figcaption>
            </figure>
          ))}
        </div>
      </section>

      <Separator className="my-12 lg:my-16" />

      <section className="space-y-6">
        <h2 className="font-[family-name:var(--font-fraunces),ui-serif,Georgia,serif] text-2xl font-semibold tracking-tight sm:text-3xl">
          What powers this project
        </h2>
        <div className="grid gap-4 md:grid-cols-3">
          {STACK_PILLARS.map((pillar) => (
            <Card key={pillar.title} className="border-[#2A2A2A] bg-[#121212]/80">
              <CardHeader className="space-y-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-sm bg-[#E10600]/10 text-[#E10600]">
                    <pillar.icon className="h-5 w-5" />
                  </div>
                  <Badge className="border-[#2A2A2A] bg-[#0A0A0A] font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                    {pillar.badge}
                  </Badge>
                </div>
                <CardTitle className="text-base font-semibold">{pillar.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-relaxed text-muted-foreground">{pillar.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}
