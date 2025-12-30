export type CanonicalStats = {
    minutes: number;
    goal: number;
    assist: number;
    yellowCard: number;
    redCard: number;
    chancesCreated: number;
    bigChancesCreated: number;
    tackles: number;
    interceptions: number;
    recoveries: number;
    penaltyWon: number;
    possWonAtt3rd: number;
    bigChanceMissed: number;
    expectedGoals: number;
    expectedAssists: number;
};

export type Player = {
    id: number;
    name: string;
    team?: string | null;
    league?: string | null;
    position?: string | null;
    stats: CanonicalStats;
    score: number;
    breakdown: Record<string, number>;
};
