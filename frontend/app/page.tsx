import { redirect } from "next/navigation";

/** Always send `/` to the default season. Edge/host 404s happen if this route is missing. */
export default function HomePage() {
  redirect("/season/2026");
}
