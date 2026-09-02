export type LensId = "business" | "technical";

export type ProjectStatus = "live" | "coming-soon";

export type ProjectLink = {
  label: string;
  href: string;
  external?: boolean;
};

export type ProjectSummary = {
  slug: string;
  title: string;
  subtitle: string;
  excerpt: string;
  tags: string[];
  businessHook: string;
  technicalHook: string;
  links: ProjectLink[];
  status: ProjectStatus;
  featured?: boolean;
};

export type RoadmapItem = {
  id: string;
  title: string;
  summary: string;
  unlocks: string[];
  status: "planned" | "contract-ready" | "in-design";
};

export type EvalDimension = {
  id: string;
  label: string;
  description: string;
  score: number;
  maxScore: number;
  method: string;
};

export type EvalCase = {
  id: number;
  title: string;
  query: string;
  expectedIntent: string;
  status: "pass" | "partial" | "roadmap";
  dimensions: string[];
};

export type EvalSuite = {
  name: string;
  catalogPath: string;
  dimensions: EvalDimension[];
  cases: EvalCase[];
  methods: { title: string; body: string }[];
};

export type LensMetric = {
  label: string;
  value: string;
  hint?: string;
};

export type LensSection = {
  id: string;
  title: string;
  body: string;
  bullets?: string[];
  metrics?: LensMetric[];
};

export type ProjectLensContent = {
  headline: string;
  intro: string;
  sections: LensSection[];
};
