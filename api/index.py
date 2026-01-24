from __future__ import annotations

from fastapi import FastAPI, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.database import get_db
from src.db_models import PlayerStats, Player, Team, League
from src.models import PlayerOut, CanonicalStats
from src.config import WEIGHTS

app = FastAPI(
    title="Top Players API",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# Dev local (Vite) + prod (same-origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Plus simple pour le dev, à restreindre en prod si besoin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"ok": True}

@app.get("/api/scoring/weights")
def scoring_weights():
    return WEIGHTS.__dict__

@app.get("/api/players", response_model=list[PlayerOut])
def get_players(
    league_id: int = Query(..., ge=1),
    season: str = Query("2024/2025"),
    limit: int = Query(50, ge=1, le=200),
    min_minutes: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Récupère les joueurs depuis la base de données Supabase, triés par score.
    """
    # Jointure entre PlayerStats, Player et Team
    query = (
        db.query(PlayerStats)
        .join(Player, PlayerStats.player_id == Player.player_id)
        .outerjoin(Team, Player.team_id == Team.team_id)
        .outerjoin(League, PlayerStats.competition_id == League.league_id)
        .filter(PlayerStats.competition_id == league_id)
        .filter(PlayerStats.season == season)
        .filter(PlayerStats.minutes >= min_minutes)
        .order_by(desc(PlayerStats.total_score))
        .limit(limit)
    )

    db_results = query.all()
    
    output = []
    for p_stats in db_results:
        # Re-construction du modèle Canonique
        canon = CanonicalStats(
            minutes=p_stats.minutes,
            goal=p_stats.goals,
            assist=p_stats.assists,
            yellowCard=p_stats.yellow_cards,
            redCard=p_stats.red_cards,
            chancesCreated=p_stats.chances_created,
            bigChancesCreated=p_stats.big_chances_created,
            tackles=p_stats.tackles,
            interceptions=p_stats.interceptions,
            recoveries=p_stats.recoveries,
            penaltyWon=p_stats.penalty_won,
            possWonAtt3rd=p_stats.poss_won_att_3rd,
            bigChanceMissed=p_stats.big_chance_missed,
            expectedGoals=p_stats.expected_goals,
            expectedAssists=p_stats.expected_assists
        )

        # Construction du breakdown de score
        breakdown = {
            "base_score": p_stats.base_score,
            "bonusGoalTop4": p_stats.bonus_goal_top4,
            "bonusAssistTop4": p_stats.bonus_assist_top4,
            "bonusUclQF": p_stats.bonus_ucl_qf,
            "bonusUclSF": p_stats.bonus_ucl_sf,
            "bonusUclFinal": p_stats.bonus_ucl_final,
            "bonusMotm": p_stats.bonus_motm
        }

        output.append(PlayerOut(
            id=p_stats.player_id,
            name=p_stats.player.name,
            team=p_stats.player.team.name if p_stats.player.team else "Unknown",
            league=p_stats.player.team.league.name if (p_stats.player.team and p_stats.player.team.league) else "Unknown",
            position=p_stats.player.position,
            stats=canon,
            score=p_stats.total_score,
            breakdown=breakdown
        ))

    return output
