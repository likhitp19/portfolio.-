import type { Metadata } from "next";
import Image from "next/image";
import {
  BrainCircuit,
  Database,
  FileDown,
  Github,
  Linkedin,
  Mail,
  Radar,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

export const metadata: Metadata = {
  title: "About — Apex F1 Suite",
  description:
    "Senior AI Product / Systems Engineer — agentic workflows, domain RAG, and multimodal telemetry.",
};

const PROFILE = {
  name: "Likhit P.",
  title: "Senior AI Product / Systems Engineer",
  tagline:
    "Bridging complex agentic AI systems, multimodal vision pipelines, and scalable technical product architectures.",
  email: "hello@likhit.dev",
  linkedin: "https://www.linkedin.com/in/likhitp19",
  github: "https://github.com/likhitp19",
  resumeHref: "/resume.pdf",
} as const;

const STACK_PILLARS = [
  {
    icon: BrainCircuit,
    title: "Agentic Workflows",
    badge: "LangGraph",
    description:
      "LangGraph-driven routing, tool orchestration, and resilient fallback systems that keep complex pipelines reliable under real-world failure modes.",
  },
  {
    icon: Database,
    title: "Domain-Specific RAG",
    badge: "Pinecone",
    description:
      "High-precision legal vector search with Pinecone and strict chunk metadata provenance — every citation traceable to source document and page.",
  },
  {
    icon: Radar,
    title: "Multimodal Telemetry",
    badge: "OpenF1 + Qwen-VL",
    description:
      "Fusing spatial computer vision (Qwen-VL) with high-speed time-series data (OpenF1) to ground regulatory reasoning in observable on-track evidence.",
  },
] as const;

const PURSUITS = [
  {
    title: "Rock Climbing & Bouldering",
    copy: "Visual problem solving, spatial movement, and resilience — reading routes the way systems read telemetry.",
    image: "/images/climbing.jpg",
    className: "md:col-span-2 md:row-span-2 min-h-[280px] md:min-h-0",
  },
  {
    title: "Oil Painting & Street Art",
    copy: "Tactile creativity, layering, and composition — building depth one deliberate stroke at a time.",
    image: "/images/art.jpg",
    className: "md:col-span-1 md:row-span-1 min-h-[220px]",
  },
  {
    title: "Craft Brewing & Fermentation",
    copy: "Scientific precision, recipe iteration, and patience — controlled experiments with living cultures.",
    image: "/images/brewing.jpg",
    className: "md:col-span-1 md:row-span-1 min-h-[220px]",
  },
  {
    title: "Solo Travel & Exploration",
    copy: "Cultural immersion, adaptability, and worldview — navigating unfamiliar terrain with curiosity.",
    image: "/images/travel.jpg",
    className: "md:col-span-2 md:row-span-1 min-h-[220px]",
  },
] as const;

export default function AboutPage() {
  return (
    <main className="mx-auto max-w-7xl px-6 py-10 lg:py-16">
      {/* Hero */}
      <section className="grid gap-10 lg:grid-cols-[minmax(0,280px)_1fr] lg:items-center lg:gap-16 xl:gap-20">
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
                  sizes="(max-width: 1024px) 280px, 280px"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-6 text-center lg:text-left">
          <div className="space-y-3">
            <Badge className="border-[#C8A24A]/40 bg-[#C8A24A]/10 text-[#C8A24A]">
              Creator & Engineer
            </Badge>
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
                Email
              </a>
            </Button>
            <Button asChild variant="outline" size="sm" className="border-[#2A2A2A] bg-[#121212] hover:bg-[#1A1A1A]">
              <a href={PROFILE.linkedin} target="_blank" rel="noopener noreferrer">
                <Linkedin className="h-4 w-4" />
                LinkedIn
              </a>
            </Button>
            <Button asChild variant="outline" size="sm" className="border-[#2A2A2A] bg-[#121212] hover:bg-[#1A1A1A]">
              <a href={PROFILE.github} target="_blank" rel="noopener noreferrer">
                <Github className="h-4 w-4" />
                GitHub
              </a>
            </Button>
            <Button asChild size="sm">
              <a href={PROFILE.resumeHref} download>
                <FileDown className="h-4 w-4" />
                Resume
              </a>
            </Button>
          </div>
        </div>
      </section>

      <Separator className="my-12 lg:my-16" />

      {/* Engineering Philosophy */}
      <section className="space-y-8">
        <div className="space-y-2 text-center lg:text-left">
          <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[#C8A24A]">
            Technical Core
          </p>
          <h2 className="font-[family-name:var(--font-fraunces),ui-serif,Georgia,serif] text-3xl font-semibold tracking-tight sm:text-4xl">
            The Engineering Philosophy
          </h2>
          <p className="mx-auto max-w-2xl text-muted-foreground lg:mx-0">
            Architectural stack behind the Apex F1 Suite — built for precision, traceability, and production-grade
            agentic systems.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {STACK_PILLARS.map((pillar) => (
            <Card
              key={pillar.title}
              className="group border-[#2A2A2A] bg-[#121212]/80 transition-all duration-300 hover:border-[#E10600]/30 hover:bg-[#141414]"
            >
              <CardHeader className="space-y-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-sm bg-[#E10600]/10 text-[#E10600] transition-colors duration-300 group-hover:bg-[#E10600]/20">
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

      <Separator className="my-12 lg:my-16" />

      {/* Bento Grid */}
      <section className="space-y-8">
        <div className="space-y-2 text-center lg:text-left">
          <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[#C8A24A]">
            Beyond the Terminal
          </p>
          <h2 className="font-[family-name:var(--font-fraunces),ui-serif,Georgia,serif] text-3xl font-semibold tracking-tight sm:text-4xl">
            Interests & Pursuits
          </h2>
          <p className="mx-auto max-w-2xl text-muted-foreground lg:mx-0">
            The same curiosity that drives systems design shows up off-screen — in movement, craft, and exploration.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-4 md:grid-rows-2">
          {PURSUITS.map((item) => (
            <article
              key={item.title}
              className={`group relative overflow-hidden rounded-sm border border-[#2A2A2A] bg-[#121212] ${item.className}`}
            >
              <div className="absolute inset-0">
                <Image
                  src={item.image}
                  alt={item.title}
                  fill
                  className="object-cover transition-transform duration-500 ease-out group-hover:scale-105"
                  sizes="(max-width: 768px) 100vw, 50vw"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#0A0A0A] via-[#0A0A0A]/70 to-[#0A0A0A]/20 transition-opacity duration-300 group-hover:via-[#0A0A0A]/80" />
              </div>
              <div className="relative flex h-full flex-col justify-end p-5 sm:p-6">
                <h3 className="text-lg font-semibold text-[#FAFAFA]">{item.title}</h3>
                <p className="mt-2 max-w-md text-sm leading-relaxed text-[#D4D4D4]/90">{item.copy}</p>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
