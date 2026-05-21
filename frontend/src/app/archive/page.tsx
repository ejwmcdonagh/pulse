"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchArchivedCards, type ProvocationCard } from "@/lib/api";

const DOMAIN_LABELS: Record<string, string> = {
  identity_credential:  "Identity & Credential",
  vulnerability_patch:  "Vulnerability & Patch",
  supply_chain:         "Supply Chain",
  detection_response:   "Detection & Response",
  data_exposure:        "Data Exposure",
  ransomware_extortion: "Ransomware & Extortion",
};

const SCORE_COLOUR = (score: number) =>
  score >= 70 ? "bg-red-600 text-white"
  : score >= 45 ? "bg-orange-500 text-white"
  : "bg-zinc-400 text-white";

export default function ArchivePage() {
  const [cards, setCards] = useState<ProvocationCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [before, setBefore] = useState("");

  useEffect(() => {
    setLoading(true);
    fetchArchivedCards(before || undefined)
      .then(setCards)
      .finally(() => setLoading(false));
  }, [before]);

  return (
    <div className="flex flex-col min-h-screen bg-zinc-50">
      <header className="border-b border-zinc-200 bg-white px-6 py-4 shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-zinc-900">Dismissed cards</h1>
            <p className="text-xs text-zinc-400 mt-0.5">Cards you have reviewed and dismissed from the board.</p>
          </div>
          <Link
            href="/"
            className="rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-xs font-medium text-zinc-700 hover:border-zinc-400 hover:bg-zinc-50 transition-colors"
          >
            Back to board
          </Link>
        </div>
      </header>

      <main className="flex-1 px-6 py-6 max-w-4xl mx-auto w-full">
        {/* Date filter */}
        <div className="flex items-center gap-3 mb-6">
          <label className="text-xs text-zinc-500 shrink-0">Show cards dismissed before</label>
          <input
            type="date"
            value={before}
            onChange={(e) => setBefore(e.target.value)}
            className="rounded-md border border-zinc-200 bg-white px-3 py-1.5 text-xs text-zinc-700 focus:outline-none focus:border-zinc-400"
          />
          {before && (
            <button
              onClick={() => setBefore("")}
              className="text-xs text-zinc-400 hover:text-zinc-600 transition-colors"
            >
              Clear
            </button>
          )}
        </div>

        {loading ? (
          <p className="text-sm text-zinc-400 animate-pulse">Loading...</p>
        ) : cards.length === 0 ? (
          <div className="rounded-lg border border-dashed border-zinc-200 p-8 text-center">
            <p className="text-sm text-zinc-400">No dismissed cards{before ? " before that date" : ""}.</p>
          </div>
        ) : (
          <div className="flex flex-col gap-0 rounded-lg border border-zinc-200 bg-white overflow-hidden">
            {cards.map((card, i) => (
              <div
                key={card.id}
                className={`px-5 py-4 flex items-start gap-4 ${i < cards.length - 1 ? "border-b border-zinc-100" : ""}`}
              >
                <span className={`shrink-0 mt-0.5 inline-flex items-center rounded px-2 py-0.5 text-xs font-semibold tabular-nums ${SCORE_COLOUR(card.score)}`}>
                  {card.score}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-zinc-800 leading-snug">
                    {card.signal_headline}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-zinc-400">
                      {DOMAIN_LABELS[card.risk_domain] ?? card.risk_domain}
                    </span>
                    <span className="text-zinc-300 text-xs">·</span>
                    <span className="text-xs text-zinc-400">
                      {new Date(card.generated_at).toLocaleDateString("en-GB", {
                        day: "numeric", month: "short", year: "numeric",
                      })}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {cards.length > 0 && (
          <p className="text-xs text-zinc-400 mt-3 text-right">{cards.length} dismissed {cards.length === 1 ? "card" : "cards"}</p>
        )}
      </main>
    </div>
  );
}
