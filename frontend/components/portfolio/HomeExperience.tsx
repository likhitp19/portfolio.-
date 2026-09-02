import { WORK_EXPERIENCE } from "@/lib/portfolio/profile";

export function HomeExperience() {
  return (
    <section id="experience" className="scroll-mt-20 border-b border-[#262626] py-12 md:py-16">
      <h2 className="font-serif text-2xl font-semibold text-[#FAFAFA]">Work experience</h2>
      <ul className="mt-6 space-y-8">
        {WORK_EXPERIENCE.map((job) => (
          <li key={job.role}>
            <p className="font-medium text-[#FAFAFA]">{job.role}</p>
            <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-muted-foreground">
              {job.highlights.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
    </section>
  );
}
