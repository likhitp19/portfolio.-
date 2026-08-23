"use client";

import { useState } from "react";

type AvatarProps = {
  src: string | null;
  alt: string;
  fallback: string;
  className?: string;
};

export function MediaAvatar({ src, alt, fallback, className }: AvatarProps) {
  const [failed, setFailed] = useState(false);
  if (!src || failed) {
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
      src={src}
      alt={alt}
      className={
        className ??
        "h-14 w-14 rounded-full border border-border object-cover object-top bg-secondary"
      }
      onError={() => setFailed(true)}
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
      className="h-6 w-6 object-contain"
      onError={() => setIndex((current) => current + 1)}
    />
  );
}
