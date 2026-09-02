import type { ProjectSummary } from "@/lib/portfolio/types";

export const PROJECTS: ProjectSummary[] = [
  {
    slug: "apex-f1",
    title: "Apex F1 Suite",
    subtitle: "Enterprise F1 console · commercial intelligence + regulatory simulation",
    excerpt:
      "A dark management console for constructor economics, driver asset ROI, executive Co-Pilot chat, and a multimodal Team Principal Protest Engine — one FastAPI contract, two LangGraph pipelines.",
    tags: ["LangGraph", "RAG", "Multi-agent", "FastAPI", "Next.js"],
    businessHook: "Financial telemetry, CPP efficiency, Executive Co-Pilot for championship decisions.",
    technicalHook: "SSE handoffs, Pinecone hybrid RAG, Qwen-VL vision, server-owned traces.",
    links: [
      { label: "Live demo", href: "/season/2026?tab=manufacturer" },
      { label: "Regulatory desk", href: "/steward" },
    ],
    status: "live",
    featured: true,
  },
  {
    slug: "piglow-led",
    title: "PiGlow LED Orchestra",
    subtitle: "Raspberry Pi IoT · reactive light sculpture",
    excerpt:
      "A network of PiGlow LED modules orchestrated from a web dashboard — MIDI-style sequences, ambient reactive modes, and GPIO timing experiments. Source lives in the repo `iot/` folder; case study landing soon.",
    tags: ["Raspberry Pi", "Python", "GPIO", "IoT", "WebSockets"],
    businessHook: "Physical-digital experiences that feel alive in a room, not just on a screen.",
    technicalHook: "I2C LED control, async event loops, and a lightweight LAN control plane.",
    links: [],
    status: "coming-soon",
    featured: true,
  },
];

export function getProject(slug: string): ProjectSummary | undefined {
  return PROJECTS.find((project) => project.slug === slug);
}
