import Link from "next/link";
import { Mail, Phone } from "lucide-react";

import { PROFILE } from "@/lib/portfolio/profile";

export function HomeIntro() {
  return (
    <section className="border-b border-[#262626] pb-12 pt-4 md:pb-16">
      <div className="flex flex-col gap-8 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-4">
          <h1 className="font-serif text-4xl font-semibold tracking-tight text-[#FAFAFA] sm:text-5xl">{PROFILE.name}</h1>
          <p className="text-lg text-[#C8A24A]">{PROFILE.title}</p>
          <p className="max-w-xl text-sm leading-relaxed text-muted-foreground">{PROFILE.tagline}</p>
          <p className="text-sm text-muted-foreground">
            {PROFILE.location} · {PROFILE.languages}
          </p>
        </div>

        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/images/profile.jpg"
          alt={`${PROFILE.name} profile`}
          width={96}
          height={96}
          className="h-24 w-24 shrink-0 rounded-full border border-[#262626] object-cover"
        />
      </div>

      <div className="mt-6 flex flex-wrap gap-4 text-sm">
        <a href={`mailto:${PROFILE.email}`} className="inline-flex items-center gap-2 text-muted-foreground hover:text-[#C8A24A]">
          <Mail className="h-4 w-4" />
          {PROFILE.email}
        </a>
        <a href={`tel:${PROFILE.phone}`} className="inline-flex items-center gap-2 text-muted-foreground hover:text-[#C8A24A]">
          <Phone className="h-4 w-4" />
          {PROFILE.phone}
        </a>
        <Link href="/resume.pdf" className="text-muted-foreground hover:text-[#C8A24A]">
          Resume
        </Link>
      </div>
    </section>
  );
}
