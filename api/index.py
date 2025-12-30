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
    Retourne les joueurs triés par score décroissant, en agrégeant les stats
    de la ligue, des coupes nationales et des compétitions européennes.
    """
    from src.config import LEAGUE_TO_CUPS, INTERNATIONAL_CUPS

    cache_key = f"players:v4:{league_id}:{season}:{min_minutes}:{limit}"
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

    # Déterminer toutes les compétitions à fetcher
    cids = [league_id]
    if league_id in LEAGUE_TO_CUPS:
        cids.extend(LEAGUE_TO_CUPS[league_id])
    
    # On ajoute toujours les coupes d'Europe car les joueurs de top ligues y participent
    cids.extend(INTERNATIONAL_CUPS)

    players_by_id: dict[int, PlayerOut] = {}

    for cid in cids:
        try:
            print(f"DEBUG: Fetching stats for competition {cid}...")
            # On pourrait paralléliser ici plus tard
            rows = fotmob.fetch_league_players(cid, season=season)
            for row in rows:
                payload = fotmob.to_player_payload(row, league_name=league_name)
                pid = payload["id"]
                if pid <= 0:
                    continue

                stats = payload["stats"]
                
                if pid in players_by_id:
                    existing = players_by_id[pid]
                    # Fusionner les stats
                    for field in stats.model_fields:
                        val = getattr(stats, field)
                        if isinstance(val, (int, float)):
                            current_val = getattr(existing.stats, field)
                            setattr(existing.stats, field, current_val + val)
                    
                    # Recalculer le score après fusion
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
            print(f"Error fetching/processing competition {cid}: {e}")
            continue

    # Filtrage par minutes après agrégation
    filtered_players = [
        p for p in players_by_id.values() 
        if p.stats.minutes >= min_minutes
    ]

    # Tri par score
    filtered_players.sort(key=lambda x: x.score, reverse=True)
    result = filtered_players[:limit]

    CACHE.set(cache_key, result, ttl_s=cache_ttl_s)
    return result

