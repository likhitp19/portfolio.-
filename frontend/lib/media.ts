"use client";

function key(value: string): string {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

/** Official F1 DAM last-name slugs for 2025/2026Drivers portraits. */
const DRIVER_SLUG: Record<string, string> = {
  "max verstappen": "verstappen",
  "lando norris": "norris",
  "oscar piastri": "piastri",
  "charles leclerc": "leclerc",
  "lewis hamilton": "hamilton",
  "george russell": "russell",
  "carlos sainz": "sainz",
  "sergio perez": "perez",
  "fernando alonso": "alonso",
  "lance stroll": "stroll",
  "pierre gasly": "gasly",
  "esteban ocon": "ocon",
  "alex albon": "albon",
  "alexander albon": "albon",
  "yuki tsunoda": "tsunoda",
  "nico hulkenberg": "hulkenberg",
  "kevin magnussen": "magnussen",
  "valtteri bottas": "bottas",
  "oliver bearman": "bearman",
  "franco colapinto": "colapinto",
  "liam lawson": "lawson",
  "andrea kimi antonelli": "antonelli",
  "kimi antonelli": "antonelli",
  "gabriel bortoleto": "bortoleto",
  "isack hadjar": "hadjar",
  "arvid lindblad": "lindblad",
};

const TEAM_LOGO_SLUG: Record<string, string> = {
  mclaren: "mclaren",
  ferrari: "ferrari",
  "red bull racing": "red-bull-racing",
  "red bull": "red-bull-racing",
  mercedes: "mercedes",
  "aston martin": "aston-martin",
  alpine: "alpine",
  "alpine f1 team": "alpine",
  williams: "williams",
  haas: "haas",
  "haas f1 team": "haas",
  rb: "racing-bulls",
  "rb f1 team": "racing-bulls",
  "racing bulls": "racing-bulls",
  sauber: "kick-sauber",
  "kick sauber": "kick-sauber",
  audi: "kick-sauber",
  "audi f1": "kick-sauber",
  cadillac: "cadillac",
  "cadillac f1 team": "cadillac",
};

function portraitUrl(folder: string, slug: string): string {
  return `https://media.formula1.com/image/upload/f_auto,c_limit,q_auto,w_240/content/dam/fom-website/drivers/${folder}/${slug}`;
}

export function driverHeadshotFallbacks(fullName: string): string[] {
  const slug = DRIVER_SLUG[key(fullName)] || key(fullName).split(" ").pop() || "";
  if (!slug) {
    return [];
  }
  return ["2026Drivers", "2025Drivers", "2024Drivers"].map((folder) => portraitUrl(folder, slug));
}

export function driverHeadshotUrl(fullName: string, _year = 2026): string | null {
  return driverHeadshotFallbacks(fullName)[0] ?? null;
}

function teamSlug(teamName: string): string | undefined {
  const k = key(teamName);
  if (TEAM_LOGO_SLUG[k]) {
    return TEAM_LOGO_SLUG[k];
  }
  for (const [alias, value] of Object.entries(TEAM_LOGO_SLUG)) {
    if (k.includes(alias) || alias.includes(k)) {
      return value;
    }
  }
  return undefined;
}

export function constructorLogoUrl(teamName: string, year = 2025): string | null {
  const slug = teamSlug(teamName);
  if (!slug) {
    return null;
  }
  return `https://media.formula1.com/content/dam/fom-website/teams/${year}/${slug}-logo.png`;
}

export function constructorLogoFallbacks(teamName: string): string[] {
  const slug = teamSlug(teamName);
  if (!slug) {
    return [];
  }
  const years = [2026, 2025, 2024, 2023];
  const urls = years.map((year) => `https://media.formula1.com/content/dam/fom-website/teams/${year}/${slug}-logo.png`);
  urls.push(
    `https://media.formula1.com/image/upload/c_lfill,w_80/q_auto/content/dam/fom-website/2018-redesign-assets/team%20logos/${slug}.jpg`,
  );
  if (slug === "kick-sauber") {
    urls.push(
      "https://media.formula1.com/image/upload/c_lfill,w_80/q_auto/content/dam/fom-website/2018-redesign-assets/team%20logos/kick%20sauber.jpg",
    );
  }
  if (slug === "cadillac") {
    urls.push(
      "https://media.formula1.com/content/dam/fom-website/teams/2025/williams-logo.png",
    );
  }
  return urls;
}
