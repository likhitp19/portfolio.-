import type { Metadata } from "next";
import { Fraunces, Geist, JetBrains_Mono } from "next/font/google";
import { Suspense } from "react";

import { AppHeader } from "@/components/layout/AppHeader";

import "./globals.css";

const sans = Geist({ subsets: ["latin"], variable: "--font-geist" });
const serif = Fraunces({ subsets: ["latin"], variable: "--font-fraunces" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains" });

export const metadata: Metadata = {
  title: "Likhit P. — AI Product Analyst & Engineer",
  description: "Dual-lens portfolio: business KPIs and LangGraph system design for enterprise AI products",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`dark ${sans.variable} ${serif.variable} ${mono.variable}`} style={{ colorScheme: "dark" }}>
      <body className="min-h-screen bg-background font-sans text-foreground antialiased">
        <Suspense fallback={<div className="h-14 border-b border-[#2A2A2A] bg-[#0E0E0E]/95" />}>
          <AppHeader />
        </Suspense>
        {children}
      </body>
    </html>
  );
}
