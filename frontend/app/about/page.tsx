import type { Metadata } from "next";
import { Mail, Phone } from "lucide-react";

import { Button } from "@/components/ui/button";

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
  { title: "Sunset on the water", image: "/images/sunset.jpg" },
  { title: "Northern lights", image: "/images/aurora.png" },
] as const;

export default function AboutPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <section className="flex flex-col items-center gap-8 sm:flex-row sm:items-start">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/images/profile.jpg"
          alt={`${PROFILE.name} profile`}
          width={160}
          height={160}
          className="h-40 w-40 shrink-0 rounded-full border-2 border-[#C8A24A]/40 object-cover"
        />

        <div className="space-y-4 text-center sm:text-left">
          <div className="space-y-1">
            <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-[#C8A24A]">About Me</p>
            <h1 className="text-3xl font-semibold text-[#FAFAFA]">{PROFILE.name}</h1>
            <p className="text-base font-medium text-[#E10600]">{PROFILE.title}</p>
          </div>

          <p className="text-sm leading-relaxed text-muted-foreground">{PROFILE.tagline}</p>

          <div className="flex flex-col gap-2 sm:flex-row">
            <Button asChild variant="outline" size="sm" className="border-[#2A2A2A] bg-[#121212]">
              <a href={`mailto:${PROFILE.email}`}>
                <Mail className="h-4 w-4" />
                {PROFILE.email}
              </a>
            </Button>
            <Button asChild variant="outline" size="sm" className="border-[#2A2A2A] bg-[#121212]">
              <a href={`tel:${PROFILE.phone}`}>
                <Phone className="h-4 w-4" />
                {PROFILE.phone}
              </a>
            </Button>
          </div>
        </div>
      </section>

      <section className="mt-10 space-y-4">
        <h2 className="text-lg font-semibold text-[#FAFAFA]">Life outside work</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {LIFE_PHOTOS.map((photo) => (
            <figure key={photo.title} className="overflow-hidden rounded-sm border border-[#2A2A2A]">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={photo.image}
                alt={photo.title}
                className="block max-h-64 w-full object-cover"
              />
              <figcaption className="bg-[#121212] px-3 py-2 text-xs text-muted-foreground">
                {photo.title}
              </figcaption>
            </figure>
          ))}
        </div>
      </section>
    </main>
  );
}
