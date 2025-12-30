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

    from src.config import LEAGUE_TO_CUPS, INTERNATIONAL_CUPS

    # Déterminer toutes les compétitions à fetcher
    cids = [league_id]
    if league_id in LEAGUE_TO_CUPS:
        cids.extend(LEAGUE_TO_CUPS[league_id])
    cids.extend(INTERNATIONAL_CUPS)

    # --- Étape 1: Calcul des scores de base ---
    players_by_id: dict[int, PlayerOut] = {}
    from src.logic.bonus_service import BonusService
    bonus_service = BonusService(fotmob._client)

    top4_ids = bonus_service.get_top4_teams(league_id)

    # On récupère toutes les lignes de stats agrégées
    all_rows = []
    for cid in cids:
        try:
            print(f"DEBUG: Fetching stats for competition {cid}...")
            all_rows.extend(fotmob.fetch_league_players(cid, season=season))
        except Exception:
            continue

    for row in all_rows:
        try:
            payload = fotmob.to_player_payload(row, league_name=league_name)
            pid = payload["id"]
            if pid <= 0: continue
            stats = payload["stats"]
            
            if pid in players_by_id:
                existing = players_by_id[pid]
                for field in stats.model_fields:
                    val = getattr(stats, field)
                    if isinstance(val, (int, float)):
                        setattr(existing.stats, field, getattr(existing.stats, field) + val)
            else:
                players_by_id[pid] = PlayerOut(
                    id=pid, name=payload["name"], team=payload.get("team"),
                    league=payload.get("league"), position=payload.get("position"),
                    stats=stats, score=0.0, breakdown={}, raw=payload.get("raw", {})
                )
        except Exception: continue

    # Calcul initial
    all_players = list(players_by_id.values())
    for p in all_players:
        score, breakdown = compute_score(p.stats)
        p.score = score
        p.breakdown = breakdown

    # --- Étape 2: Raffinement avec les Bonus (Top 50 seulement pour la performance) ---
    all_players.sort(key=lambda x: x.score, reverse=True)
    top_candidates = all_players[:50]

    for p in top_candidates:
        bonus_score, bonus_breakdown = bonus_service.calculate_player_bonuses(p.id, top4_ids, season=season)
        if bonus_score > 0:
            p.score += bonus_score
            p.breakdown.update(bonus_breakdown)

    # Filtrage et tri final
    filtered_players = [p for p in all_players if p.stats.minutes >= min_minutes]
    filtered_players.sort(key=lambda x: x.score, reverse=True)
    result = filtered_players[:limit]


    CACHE.set(cache_key, result, ttl_s=cache_ttl_s)
    return result

