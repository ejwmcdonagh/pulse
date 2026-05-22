"use client";

import { useState, useTransition } from "react";
import type { BuiltinSource } from "@/lib/api";
import { apiFetch } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function BuiltinSourcesForm({ initialSources }: { initialSources: BuiltinSource[] }) {
  const [sources, setSources] = useState<BuiltinSource[]>(initialSources);
  const [isPending, startTransition] = useTransition();

  const toggle = (id: string) => {
    startTransition(async () => {
      const res = await apiFetch(`${API_BASE}/api/profile/sources/builtin/${id}/toggle`, {
        method: "PATCH",
      });
      if (!res.ok) return;
      const data = await res.json();
      setSources((prev) =>
        prev.map((s) => (s.id === id ? { ...s, enabled: data.enabled } : s))
      );
    });
  };

  return (
    <div className="rounded-lg border border-zinc-200 bg-white divide-y divide-zinc-100">
      {sources.map((source) => (
        <div key={source.id} className="flex items-center justify-between gap-4 px-4 py-3">
          <div className="flex flex-col min-w-0">
            <span className={`text-sm font-medium ${source.enabled ? "text-zinc-900" : "text-zinc-400"}`}>
              {source.name}
            </span>
            <span className="text-xs text-zinc-400">{source.description}</span>
          </div>
          <button
            onClick={() => toggle(source.id)}
            disabled={isPending}
            className={`shrink-0 rounded-full px-3 py-1 text-xs font-medium transition-colors disabled:opacity-50 ${
              source.enabled
                ? "bg-green-100 text-green-800 hover:bg-green-200"
                : "bg-zinc-100 text-zinc-500 hover:bg-zinc-200"
            }`}
          >
            {source.enabled ? "Active" : "Paused"}
          </button>
        </div>
      ))}
    </div>
  );
}
