import type { Metadata } from "next";
import { Fraunces, Geist, JetBrains_Mono } from "next/font/google";

import "./globals.css";

const sans = Geist({ subsets: ["latin"], variable: "--font-geist" });
const serif = Fraunces({ subsets: ["latin"], variable: "--font-fraunces" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains" });

export const metadata: Metadata = {
  title: "Apex Analytics — F1 commercial desk",
  description: "Constructor valuations, cost per point, and traced multi-agent analysis",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`dark ${sans.variable} ${serif.variable} ${mono.variable}`} style={{ colorScheme: "dark" }}>
      <body className="min-h-screen bg-background font-sans text-foreground antialiased">{children}</body>
    </html>
  );
}
