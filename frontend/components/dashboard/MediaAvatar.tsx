"use client";

import { useState } from "react";

type AvatarProps = {
  src?: string | null;
  urls?: string[];
  alt: string;
  fallback: string;
  className?: string;
};

export function MediaAvatar({ src, urls, alt, fallback, className }: AvatarProps) {
  const chain = (urls && urls.length ? urls : src ? [src] : []).filter(Boolean) as string[];
  const [index, setIndex] = useState(0);
  const current = chain[index];
  if (!current) {
    return (
      <div
        className={
          className ??
          "flex h-14 w-14 items-center justify-center overflow-hidden rounded-full border border-border bg-secondary text-sm font-bold tracking-wide"
        }
      >
        {fallback}
      </div>
    );
  }
  return (
    <img
      src={current}
      alt={alt}
      className={
        className ??
        "h-14 w-14 rounded-full border border-border object-cover object-top bg-secondary"
      }
      onError={() => setIndex((value) => value + 1)}
    />
  );
}

type LogoProps = {
  urls: string[];
  alt: string;
};

export function TeamLogo({ urls, alt }: LogoProps) {
  const [index, setIndex] = useState(0);
  const src = urls[index];
  if (!src) {
    return null;
  }
  return (
    <img
      src={src}
      alt={alt}
      className="h-7 w-7 shrink-0 object-contain"
      onError={() => setIndex((current) => current + 1)}
    />
  );
}
