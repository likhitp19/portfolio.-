import { EDUCATION } from "@/lib/portfolio/profile";

export function HomeEducation() {
  return (
    <section id="education" className="scroll-mt-20 border-b border-[#262626] py-12 md:py-16">
      <h2 className="font-serif text-2xl font-semibold text-[#FAFAFA]">Education</h2>
      <ul className="mt-6 space-y-5">
        {EDUCATION.map((item) => (
          <li key={item.degree} className="border-l-2 border-[#262626] pl-4">
            <p className="font-medium text-[#FAFAFA]">{item.degree}</p>
            <p className="text-sm text-muted-foreground">{item.school}</p>
            <p className="text-sm text-[#C8A24A]">{item.years}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
