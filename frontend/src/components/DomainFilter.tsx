"use client";

import { DOMAINS } from "@/lib/api";

type Props = {
  selected: string | null;
  onChange: (domain: string | null) => void;
};

export default function DomainFilter({ selected, onChange }: Props) {
  return (
    <div className="flex items-center gap-2 flex-wrap">
      <span className="text-xs text-zinc-400 shrink-0">Filter by domain</span>
      <div className="flex gap-1.5 flex-wrap">
        <button
          onClick={() => onChange(null)}
          className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
            selected === null
              ? "bg-zinc-800 text-white"
              : "border border-zinc-300 text-zinc-600 hover:border-zinc-400 hover:bg-zinc-50"
          }`}
        >
          All
        </button>
        {DOMAINS.map((domain) => (
          <button
            key={domain.id}
            onClick={() => onChange(selected === domain.id ? null : domain.id)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              selected === domain.id
                ? "bg-zinc-800 text-white"
                : "border border-zinc-300 text-zinc-600 hover:border-zinc-400 hover:bg-zinc-50"
            }`}
          >
            {domain.label}
          </button>
        ))}
      </div>
    </div>
  );
}
