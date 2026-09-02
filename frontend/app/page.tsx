import type { Metadata } from "next";

import { HomeEducation } from "@/components/portfolio/HomeEducation";
import { HomeExperience } from "@/components/portfolio/HomeExperience";
import { HomeIntro } from "@/components/portfolio/HomeIntro";
import { HomeProjects } from "@/components/portfolio/HomeProjects";
import { PortfolioShell } from "@/components/portfolio/layout/PortfolioShell";
import { PROFILE } from "@/lib/portfolio/profile";

export const metadata: Metadata = {
  title: `${PROFILE.name} — ${PROFILE.title}`,
  description: PROFILE.tagline,
};

export default function HomePage() {
  return (
    <PortfolioShell>
      <HomeIntro />
      <HomeEducation />
      <HomeExperience />
      <HomeProjects />
    </PortfolioShell>
  );
}
