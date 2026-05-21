"use client";

import { useState } from "react";
import type { ProvocationCard, RiskDomain } from "@/lib/api";
import SwimLanes from "./SwimLanes";
import TeamFilter from "./TeamFilter";
import DomainFilter from "./DomainFilter";

type Props = {
  cards: ProvocationCard[];
  domains: RiskDomain[];
  technologies: string[];
};

export default function Dashboard({ cards, domains, technologies }: Props) {
  const [selectedTeam, setSelectedTeam] = useState<string | null>(null);
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null);

  let visibleCards = cards;

  if (selectedTeam) {
    visibleCards = visibleCards.filter((c) => c.affected_teams?.includes(selectedTeam));
  }

  // Filter by all_domains (not just primary) so cross-lane cards are included
  if (selectedDomain) {
    visibleCards = visibleCards.filter((c) =>
      (c.metadata.all_domains ?? [c.risk_domain]).includes(selectedDomain)
    );
  }

  return (
    <div className="flex flex-col gap-3 h-full">
      <DomainFilter selected={selectedDomain} onChange={setSelectedDomain} />
      <TeamFilter selected={selectedTeam} onChange={setSelectedTeam} />
      <SwimLanes cards={visibleCards} domains={domains} technologies={technologies} />
    </div>
  );
}
