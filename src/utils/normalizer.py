from __future__ import annotations
from typing import Any, Dict, Iterable
from src.models import CanonicalStats

# Alias possibles -> clé canonique
STAT_ALIASES: Dict[str, str] = {
    # goals / assists
    "goals": "goal",
    "goal": "goal",
    "g": "goal",

    "assists": "assist",
    "assist": "assist",
    "a": "assist",

    # cards
    "yellowcard": "yellowCard",
    "yellow_card": "yellowCard",
    "yellowcards": "yellowCard",
    "yc": "yellowCard",

    "redcard": "redCard",
    "red_card": "redCard",
    "redcards": "redCard",
    "rc": "redCard",

    # chances
    "chancescreated": "chancesCreated",
    "chances_created": "chancesCreated",
    "total_att_assist": "chancesCreated",
    "keypasses": "chancesCreated",  # souvent équivalent “chances created”

    "bigchancescreated": "bigChancesCreated",
    "big_chances_created": "bigChancesCreated",
    "big_chance_created": "bigChancesCreated",

    # defensive
    "tackles": "tackles",
    "total_tackle": "tackles",
    "interceptions": "interceptions",
    "interception": "interceptions",
    "recoveries": "recoveries",
    "penalty_won": "penaltyWon",
    "penaltywon": "penaltyWon",
    "poss_won_att_3rd": "possWonAtt3rd",
    "big_chance_missed": "bigChanceMissed",
    "bigchancemissed": "bigChanceMissed",

    # xG / xA
    "expected_goals": "expectedGoals",
    "xg": "expectedGoals",
    "expected_assists": "expectedAssists",
    "xa": "expectedAssists",

    # minutes
    "goal_assist": "assist",
    "yellow_card": "yellowCard",
    "red_card": "redCard",
    "mins_played": "minutes",
    "minutes": "minutes",
    "minutesplayed": "minutes",
    "mins": "minutes",
    "min": "minutes",
}

def _normalize_key(k: str) -> str:
    return k.strip().lower().replace(" ", "").replace("-", "_")

# List of keys known to be per-90 in FotMob's detailed response
PER_90_KEYS = {
    "total_tackle", 
    "interception", 
    "won_contest", 
    "total_scoring_att", 
    "ontarget_scoring_att", 
    "accurate_pass", 
    "fouls", 
    "saves",
    "goals_conceded",
    "poss_won_att_3rd"
}

def canonicalize_stats(raw: Dict[str, Any]) -> CanonicalStats:
    canon: Dict[str, float] = {}

    # Extract minutes for per-90 conversion
    # row from detailed fetch has 'MinutesPlayed', row from summary has 'minutes' or nothing
    minutes = float(raw.get("MinutesPlayed") or raw.get("minutes") or raw.get("minutes_played") or 0.0)

    def _get_val(k: str, v: Any) -> float:
        try:
            val = float(v) if v is not None else 0.0
            nk = _normalize_key(str(k))
            # If the stat is a per-90 rate, convert it to an absolute total
            if nk in PER_90_KEYS and minutes > 0:
                return (val * minutes) / 90.0
            return val
        except Exception:
            return 0.0

    # Handling the "stat_name" + "value" pattern (Summary/Leaderboard)
    leaderboard_key = raw.get("stat_name")
    
    # StatValue (Detailed), value (Summary), StatValueCount (Alternative)
    leaderboard_val = raw.get("StatValue") or raw.get("value") or raw.get("StatValueCount")
    
    if leaderboard_key and leaderboard_val is not None:
        target = STAT_ALIASES.get(_normalize_key(str(leaderboard_key)))
        if target:
            canon[target] = _get_val(str(leaderboard_key), leaderboard_val)

    for k, v in raw.items():
        if k in ("StatValue", "value", "StatValueCount", "stat_name"):
            continue
            
        nk = _normalize_key(str(k))
        target = STAT_ALIASES.get(nk)
        if not target:
            continue
            
        val = _get_val(k, v)
        if target not in canon:
            canon[target] = val

    # Final rounding to integers for all stats
    for k, v in canon.items():
        if k != "minutes":
            canon[k] = float(round(v))

    # minutes en int
    canon["minutes"] = int(minutes)

    return CanonicalStats(**canon)
