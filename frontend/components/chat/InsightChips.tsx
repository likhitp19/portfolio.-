"use client";

import { Button } from "@/components/ui/button";
import type { InsightChip } from "@/lib/chips";

export function InsightChips({
  chips,
  disabled,
  onSelect,
}: {
  chips: InsightChip[];
  disabled?: boolean;
  onSelect: (chip: InsightChip) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {chips.map((chip) => (
        <Button
          key={chip.id}
          type="button"
          variant="outline"
          size="sm"
          disabled={disabled}
          className="rounded-full border-[color:var(--gold)]/25 bg-black/20 text-[11px] uppercase tracking-[0.14em] text-[color:var(--gold)] hover:border-[color:var(--gold)]/60 hover:bg-[color:var(--gold)]/10"
          onClick={() => onSelect(chip)}
        >
          {chip.label}
        </Button>
      ))}
    </div>
  );
}
