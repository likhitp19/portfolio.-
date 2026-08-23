"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function HomePage() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/season/2025");
  }, [router]);

  return (
    <main className="flex min-h-[50vh] items-center justify-center p-8">
      <p className="text-sm text-muted-foreground">
        Opening the 2025 season…{" "}
        <a className="underline" href="/season/2025">
          Continue
        </a>
      </p>
    </main>
  );
}
