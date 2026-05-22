"use client";

import { useState, useTransition } from "react";
import { apiFetch } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function BlockedTechForm({
  initialBlocked,
}: {
  initialTechnologies: string[];
  initialBlocked: string[];
}) {
  const [blocked, setBlocked] = useState<string[]>(initialBlocked);
  const [input, setInput] = useState("");
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const add = () => {
    const value = input.trim();
    if (!value || blocked.includes(value)) return;
    setBlocked((prev) => [...prev, value].sort());
    setInput("");
    setSaved(false);
  };

  const remove = (tech: string) => {
    setBlocked((prev) => prev.filter((t) => t !== tech));
    setSaved(false);
  };

  const save = () => {
    setError(null);
    startTransition(async () => {
      // Only send blocked_technologies - the backend now handles partial updates
      // so this cannot accidentally overwrite the tech stack saved by TechProfileForm
      const res = await apiFetch(`${API_BASE}/api/profile`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ blocked_technologies: blocked }),
      });
      if (!res.ok) {
        setError("Failed to save. Please try again.");
        return;
      }
      setSaved(true);
    });
  };

  return (
    <div className="rounded-lg border border-zinc-200 bg-white p-5 flex flex-col gap-4">
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && add()}
          placeholder="e.g. Oracle, SAP, IBM, iOS"
          className="flex-1 rounded-md border border-zinc-300 px-3 py-2 text-sm placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-400"
        />
        <button
          onClick={add}
          disabled={!input.trim()}
          className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-40 transition-colors"
        >
          Add
        </button>
      </div>

      {blocked.length === 0 ? (
        <p className="text-sm text-zinc-400">No technologies hidden yet.</p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {blocked.map((tech) => (
            <span
              key={tech}
              className="inline-flex items-center gap-1.5 rounded-full bg-red-50 border border-red-200 px-3 py-1 text-sm text-red-800"
            >
              {tech}
              <button
                onClick={() => remove(tech)}
                className="text-red-400 hover:text-red-700 transition-colors"
                aria-label={`Remove ${tech}`}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      <div className="flex items-center gap-3 pt-1 border-t border-zinc-100">
        <button
          onClick={save}
          disabled={isPending}
          className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-40 transition-colors"
        >
          {isPending ? "Saving..." : "Save"}
        </button>
        {saved && <span className="text-sm text-green-600">Saved</span>}
        {error && <span className="text-sm text-red-600">{error}</span>}
      </div>
    </div>
  );
}
