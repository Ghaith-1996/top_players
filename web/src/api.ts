import type { Player } from "./types";

export interface FetchPlayersParams {
    leagueId: number;
    season: string;
    minMinutes?: number;
    limit?: number;
}

export async function fetchPlayers(params: FetchPlayersParams): Promise<Player[]> {
    const { leagueId, season, minMinutes = 0, limit = 50 } = params;
    // Use window.location.origin as base to allow relative paths
    const url = new URL("/api/players", window.location.origin);
    url.searchParams.set("league_id", String(leagueId));
    url.searchParams.set("season", season);
    url.searchParams.set("min_minutes", String(minMinutes));
    url.searchParams.set("limit", String(limit));

    const res = await fetch(url.toString());
    if (!res.ok) {
        throw new Error(`API error: ${res.statusText}`);
    }
    return (await res.json()) as Player[];
}
