import type { Metadata } from "next";
import { Fraunces, Geist, JetBrains_Mono } from "next/font/google";

import { SuiteHeader } from "@/components/layout/SuiteHeader";

import "./globals.css";

const sans = Geist({ subsets: ["latin"], variable: "--font-geist" });
const serif = Fraunces({ subsets: ["latin"], variable: "--font-fraunces" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains" });

export const metadata: Metadata = {
  title: "Apex F1 Suite",
  description: "Commercial desk + Regulatory Protest Engine for Formula 1 portfolio demos",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`dark ${sans.variable} ${serif.variable} ${mono.variable}`} style={{ colorScheme: "dark" }}>
      <body className="min-h-screen bg-background font-sans text-foreground antialiased">
        <SuiteHeader />
        {children}
      </body>
    </html>
  );
}
