from __future__ import annotations

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from src.cache import CACHE
from src.config import DEFAULT_CACHE_TTL_S, DEFAULT_LIMIT, DEFAULT_MIN_MINUTES, WEIGHTS
from src.models import PlayerOut
from src.logic.fotmob_service import FotmobService
from src.logic.scoring_service import compute_score

app = FastAPI(
    title="Top Players API",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# Dev local (Vite) + prod (same-origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fotmob = FotmobService()

@app.get("/api/health")
def health():
    return {"ok": True}

@app.get("/api/scoring/weights")
def scoring_weights():
    return WEIGHTS.__dict__

@app.get("/api/players", response_model=list[PlayerOut])
def get_players(
    league_id: int = Query(..., ge=1),
    season: str = Query(None),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=200),
    min_minutes: int = Query(DEFAULT_MIN_MINUTES, ge=0, le=10_000),
    cache_ttl_s: int = Query(DEFAULT_CACHE_TTL_S, ge=0, le=3600),
):
    """
    Retourne les joueurs triés par score décroissant.
    """
    # Reverting to simple cache key format (v3 to invalidate previous)
    cache_key = f"players:v3:{league_id}:{season}:{min_minutes}:{limit}"
    cached = CACHE.get(cache_key)
    if cached is not None:
        return cached

    LEAGUE_MAP = {
        47: "Premier League",
        87: "La Liga",
        54: "Bundesliga",
        55: "Serie A",
        53: "Ligue 1"
    }
    league_name = LEAGUE_MAP.get(league_id, "Unknown League")

    rows = fotmob.fetch_league_players(league_id, season=season)
    players_by_id: dict[int, PlayerOut] = {}

    for row in rows:
        try:
            payload = fotmob.to_player_payload(row, league_name=league_name)
            pid = payload["id"]
            if pid <= 0:
                continue

            stats = payload["stats"]
            # Skip if below min minutes (if data available)
            if stats.minutes > 0 and stats.minutes < min_minutes:
                continue

            if pid in players_by_id:
                # Fusionner les stats (cas rare intra-ligue, mais possible)
                existing = players_by_id[pid]
                for field in stats.model_fields:
                    if field == "minutes":
                        existing.stats.minutes = max(existing.stats.minutes, stats.minutes)
                        continue
                    val = getattr(stats, field)
                    if isinstance(val, (int, float)):
                        setattr(existing.stats, field, getattr(existing.stats, field) + val)

                score, breakdown = compute_score(existing.stats)
                existing.score = score
                existing.breakdown = breakdown
            else:
                score, breakdown = compute_score(stats)
                players_by_id[pid] = PlayerOut(
                    id=pid,
                    name=payload["name"],
                    team=payload.get("team"),
                    league=payload.get("league"),
                    position=payload.get("position"),
                    stats=stats,
                    score=score,
                    breakdown=breakdown,
                    raw=payload.get("raw", {}),
                )
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error processing row: {e}")
            continue

    # Sort by score
    all_players = list(players_by_id.values())
    all_players.sort(key=lambda x: x.score, reverse=True)
    result = all_players[:limit]

    CACHE.set(cache_key, result, ttl_s=cache_ttl_s)
    return result
