"use client";

function key(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

/** OpenF1 / F1 DAM driver folder codes. Fallback: initials if the CDN 404s. */
const DRIVER_CODES: Record<string, string> = {
  "max verstappen": "MAXVER01",
  "lando norris": "LANNOR01",
  "oscar piastri": "OSCPIA01",
  "charles leclerc": "CHALEC01",
  "lewis hamilton": "LEWHAM01",
  "george russell": "GEORUS01",
  "carlos sainz": "CARSAI01",
  "sergio perez": "SERPER01",
  "fernando alonso": "FERALO01",
  "lance stroll": "LANSTR01",
  "pierre gasly": "PIEGAS01",
  "esteban ocon": "ESTOCO01",
  "alex albon": "ALEALB01",
  "alexander albon": "ALEALB01",
  "yuki tsunoda": "YUKTSU01",
  "daniel ricciardo": "DANRIC01",
  "nico hulkenberg": "NICHUL01",
  "nico hülkenberg": "NICHUL01",
  "kevin magnussen": "KEVMAG01",
  "valtteri bottas": "VALBOT01",
  "zhou guanyu": "GUAZHO01",
  "guanyu zhou": "GUAZHO01",
  "logan sargeant": "LOGSAR01",
  "oliver bearman": "OLIBEA01",
  "franco colapinto": "FRACOL01",
  "liam lawson": "LIALAW01",
  "jack doohan": "JACDOO01",
  "andrea kimi antonelli": "ANDANT01",
  "kimi antonelli": "ANDANT01",
  "gabriel bortoleto": "GABBOR01",
  "isack hadjar": "ISAHAD01",
  "oliver googan": "OLIGOO01",
};

const TEAM_LOGO_SLUG: Record<string, string> = {
  mclaren: "mclaren",
  ferrari: "ferrari",
  "red bull racing": "red-bull-racing",
  mercedes: "mercedes",
  "aston martin": "aston-martin",
  alpine: "alpine",
  williams: "williams",
  haas: "haas",
  rb: "racing-bulls",
  "racing bulls": "racing-bulls",
  sauber: "kick-sauber",
  "kick sauber": "kick-sauber",
};

export function driverHeadshotUrl(fullName: string, year = 2025): string | null {
  const code = DRIVER_CODES[key(fullName)];
  if (!code) {
    return null;
  }
  const letter = code[0];
  return `https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/${letter}/${code}/${code.toLowerCase()}.png.transform/1col/image.png`;
}

export function constructorLogoUrl(teamName: string, year = 2025): string | null {
  const k = key(teamName);
  let slug: string | undefined = TEAM_LOGO_SLUG[k];
  if (!slug) {
    for (const [alias, value] of Object.entries(TEAM_LOGO_SLUG)) {
      if (k.includes(alias) || alias.includes(k)) {
        slug = value;
        break;
      }
    }
  }
  if (!slug) {
    return null;
  }
  return `https://media.formula1.com/content/dam/fom-website/teams/${year}/${slug}-logo.png`;
}

export function constructorLogoFallbacks(teamName: string): string[] {
  const years = [2025, 2024, 2023];
  return years
    .map((year) => constructorLogoUrl(teamName, year))
    .filter((url): url is string => Boolean(url));
}
