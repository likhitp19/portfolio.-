import Link from "next/link";

import { ProjectCard } from "@/components/portfolio/ProjectCard";
import { PROJECTS } from "@/lib/portfolio/projects";
import { RELEVANT_PROJECTS } from "@/lib/portfolio/profile";

export function HomeProjects() {
  const featured = PROJECTS.filter((project) => project.featured);

  return (
    <section id="projects" className="scroll-mt-20 py-12 md:py-16">
      <h2 className="font-serif text-2xl font-semibold text-[#FAFAFA]">Projects</h2>

      <div className="mt-8">
        <p className="text-sm font-medium uppercase tracking-wider text-muted-foreground">Portfolio builds</p>
        <div className="mt-4 grid gap-6 md:grid-cols-2">
          {featured.map((project) => (
            <ProjectCard key={project.slug} project={project} />
          ))}
        </div>
      </div>

      <div className="mt-12">
        <p className="text-sm font-medium uppercase tracking-wider text-muted-foreground">Other relevant work</p>
        <ul className="mt-4 space-y-6">
          {RELEVANT_PROJECTS.map((project) => (
            <li key={project.title} className="rounded-sm border border-[#262626] bg-[#121212] p-5">
              <p className="font-medium text-[#FAFAFA]">{project.title}</p>
              <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-muted-foreground">
                {project.bullets.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      </div>

      <p className="mt-8 text-sm text-muted-foreground">
        Apex F1 live demo:{" "}
        <Link href="/season/2026?tab=manufacturer" className="text-[#C8A24A] hover:underline">
          Open dashboard
        </Link>
        {" · "}
        <Link href="https://github.com/likhitp19/portfolio.-" className="text-[#C8A24A] hover:underline">
          GitHub
        </Link>
      </p>
    </section>
  );
}
