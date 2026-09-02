export const PROFILE = {
  name: "Likhit P.",
  title: "AI Product Analyst & Engineer",
  location: "Bangalore",
  languages: "English, Hindi & Kannada (Professional)",
  email: "likhit.p19@gmail.com",
  phone: "+918123856002",
  tagline:
    "AI product specialist — discovery, multi-agent systems, and full-stack delivery from customer interviews to deployed demos.",
} as const;

export const EDUCATION = [
  {
    degree: "Bachelor of Engineering (Mechatronics)",
    school: "Visvesvaraya Technological University",
    years: "2011 – 2015",
  },
  {
    degree: "Master of Science (Industrial Economics)",
    school: "Kungliga Tekniska högskolan (KTH)",
    years: "2020 – 2021",
  },
  {
    degree: "Post-Graduate Diploma (AI Business Consulting)",
    school: "Hyper Island",
    years: "2023 – 2025",
  },
] as const;

export const WORK_EXPERIENCE = [
  {
    role: "AI Product Specialist II",
    highlights: [
      "AI candidate screening and evaluation",
      "Customer service automation",
      "Discovery and development for an English learning app",
    ],
  },
  {
    role: "AI Product Development",
    highlights: ["Product and feature discovery", "Customer interviews", "Vibe coding and rapid prototyping"],
  },
  {
    role: "Customer Success",
    highlights: [
      "Interviewed marketing agencies to map workflows",
      "Tailored solutions to client specifications",
    ],
  },
] as const;

export const RELEVANT_PROJECTS = [
  {
    title: "Customer Churn Prediction",
    bullets: [
      "Prediction model using XGBoost",
      "Churn indicators through demographic and behavioral analysis",
      "Delivered actionable insights",
    ],
  },
  {
    title: "AI-Powered Workforce Management System",
    bullets: [
      "Scheduling system using Google Gemini, Vertex AI Studio, and Google OR-Tools",
      "Automated scheduling with Gen AI for last-minute anomaly handling",
      "Won second place in the hackathon",
    ],
  },
  {
    title: "AI Business Research Agent",
    bullets: [
      "AI-driven research and validation using agents",
      "Low-cost business research tool to complement traditional consulting",
      "Presented to IKEA — received excellent feedback",
    ],
  },
  {
    title: "AI-Powered Privacy Scanner & Cookie Classifier",
    bullets: [
      "Analyzed privacy policies for GDPR compliance",
      "Classified cookies using an agentic framework",
      "Human-in-the-loop system to flag anomalies",
    ],
  },
] as const;
