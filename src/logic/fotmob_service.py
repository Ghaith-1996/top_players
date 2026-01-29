from __future__ import annotations
from typing import Any, Dict, List, Optional

from mobfot import MobFot  # plus robuste que pyfotmob
from src.utils.normalizer import canonicalize_stats

def _extract_player_rows(payload: Any) -> List[Dict[str, Any]]:
    """
    pyfotmob renvoie parfois des structures différentes selon endpoint/version.
    On essaie plusieurs chemins “probables”.
    """
    if isinstance(payload, list):
        return [p for p in payload if isinstance(p, dict)]

    if not isinstance(payload, dict):
        return []

    # cas direct
    for key in ("players", "playerStats", "all_players", "player_stats"):
        v = payload.get(key)
        if isinstance(v, list):
            # Mobfot returns a list of categories (Top Scorer, Top Assists...)
            # We look for 'topThree' or 'players' in each category
            if v and isinstance(v[0], dict) and ("players" in v[0] or "topThree" in v[0]):
                flattened = []
                for category in v:
                    # 'topThree' exists in the summary view
                    if isinstance(category.get("topThree"), list):
                        # On injecte le nom de la stat dans chaque ligne pour que le normalizer sache quoi en faire
                        stat_name = category.get("name")
                        for p in category["topThree"]:
                            p["stat_name"] = stat_name
                            flattened.append(p)
                    # 'players' might exist in detailed views
                    if isinstance(category.get("players"), list):
                        stat_name = category.get("name")
                        for p in category["players"]:
                            p["stat_name"] = stat_name
                            flattened.append(p)
                return flattened
            return [p for p in v if isinstance(p, dict)]

    # cas top_stats/topStats
    ts = payload.get("top_stats") or payload.get("topStats")
    if isinstance(ts, list):
        for block in ts:
            if isinstance(block, dict):
                if isinstance(block.get("players"), list):
                    return [p for p in block["players"] if isinstance(p, dict)]
                if isinstance(block.get("stats"), list):
                    return [p for p in block["stats"] if isinstance(p, dict)]
    if isinstance(ts, dict):
        for _, block in ts.items():
            if isinstance(block, dict) and isinstance(block.get("players"), list):
                return [p for p in block["players"] if isinstance(p, dict)]

    return []

def _get_int(row: Dict[str, Any], *keys: str, default: int = 0) -> int:
    # On ajoute ParticiantId (typo dans l'API Fotmob) et d'autres variations
    all_keys = list(keys) + ["ParticiantId", "ParticipantId", "id", "playerId"]
    for k in all_keys:
        v = row.get(k)
        if v is None and "participant" in row:
            v = row["participant"].get(k)
        if v is None:
            continue
        try:
            return int(v)
        except Exception:
            continue
    return default

def _get_str(row: Dict[str, Any], *keys: str, default: Optional[str] = None) -> Optional[str]:
    for k in keys:
        v = row.get(k)
        if v is None and "participant" in row:
            v = row["participant"].get(k)
        if v is not None:
            s = str(v).strip()
            if s:
                return s
    return default

def _get_player_name(row: Dict[str, Any]) -> str:
    """Spécifique pour le nom du joueur car FotMob utilise souvent des clés très variées."""
    return _get_str(row, "ParticipantName", "name", "playerName", "player_name", "ParticipantShortName", default="Unknown") or "Unknown"



class FotmobService:
    def __init__(self) -> None:
        self._client = MobFot()

    def fetch_league_players(self, league_id: int, season: str = None) -> List[Dict[str, Any]]:
        import requests
        session = requests.Session()
        
        # mobfot utilise get_league
        if season:
            data = self._client.get_league(league_id, season=season)
        else:
            data = self._client.get_league(league_id)
        # on cherche dans data['stats']
        stats_payload = data.get("stats") or data
        categories = stats_payload.get("players")
        if categories is None:
            categories = []
        
        all_flattened_rows = []
        
        # On limite le nombre de catégories à fetch pour la performance
        # mais on prend les plus importantes
        target_stats = {
            "goals", 
            "goal_assist", 
            "yellow_card", 
            "red_card", 
            "mins_played", 
            "big_chance_created", 
            "total_att_assist",
            "total_tackle",
            "interception",
            "penalty_won",
            "poss_won_att_3rd",
            "big_chance_missed"
        }
        
        for cat in categories:
            cat_name = cat.get("name")
            fetch_url = cat.get("fetchAllUrl")
            
            # On essaie de charger la liste complète si c'est une stat intéressante
            fetched_detailed = False
            if fetch_url and (not target_stats or cat_name in target_stats):
                try:
                    res = session.get(fetch_url, timeout=5)
                    if res.status_code == 200:
                        detail_data = res.json()
                        # Structure habituelle : {"TopLists": [{"StatList": [...]}]}
                        top_lists = detail_data.get("TopLists", [])
                        for tl in top_lists:
                            for p in tl.get("StatList", []):
                                p["stat_name"] = cat_name
                                all_flattened_rows.append(p)
                        fetched_detailed = True
                except Exception as e:
                    print(f"DEBUG: Failed to fetch {fetch_url}: {e}")
            
            # On ne rajoute le topThree que si on n'a pas pu fetch la version complète
            # pour éviter les doublons (les 3 premiers sont dans le fetchAllUrl)
            if not fetched_detailed and "topThree" in cat:
                for p in cat["topThree"]:
                    p["stat_name"] = cat_name
                    all_flattened_rows.append(p)

        # Si on n'a rien trouvé via fetchAllUrl, on fallback sur l'ancien extracteur
        if not all_flattened_rows:
            return _extract_player_rows(stats_payload)
            
        return all_flattened_rows

    def get_league_team_ids(self, league_id: int, season: str = None) -> set[int]:
        """Récupère tous les IDs d'équipes valides pour cette ligue (via le classement/table)."""
        import requests
        try:
            if season:
                data = self._client.get_league(league_id, season=season)
            else:
                data = self._client.get_league(league_id)
            
            team_ids = set()
            tables = data.get("table", [])
            if isinstance(tables, list):
                for t in tables:
                    # Structure: t['data']['table']['all'] -> list of teams
                    t_data = t.get("data", {})
                    if "table" in t_data:
                        inner = t_data["table"]
                        # 'all' contient le classement général
                        teams = inner.get("all", [])
                        for team in teams:
                            tid = team.get("id")
                            if tid:
                                team_ids.add(int(tid))
            return team_ids
        except Exception as e:
            print(f"Error fetching team IDs for league {league_id}: {e}")
            return set()

    def to_player_payload(self, row: Dict[str, Any], league_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Transforme un “row” en structure standard (id, name, team, position, stats canon).
        """
        player_id = _get_int(row, "id", "playerId", "player_id", default=0)
        name = _get_player_name(row)
        team = _get_str(row, "teamName", "TeamName", "team_name", "club", "team", default=None)
        
        # FIX: Manual extraction of team_id to avoid _get_int's PlayerId fallbacks
        team_id = 0
        # Priority keys
        for key in ["TeamId", "teamId", "team_id", "contestantId", "participantId"]:
             val = row.get(key)
             if val is not None:
                 try:
                     team_id = int(val)
                     # If we found a plausible ID (not 0), stop. 
                     # Note: participantId IS risky if it's actually the player, but sometimes it's the team in team-lists. 
                     # In 'StatList', ParticipantId is Player, TeamId is Team. 
                     # So we prioritize TeamId.
                     if team_id > 0:
                         break
                 except:
                     pass
        
        position = _get_str(row, "position", "pos", "positionDescription", default=None)

        # stats peuvent être directement dans row ou sous row["stats"]
        stats_raw: Dict[str, Any] = {}
        if isinstance(row.get("stats"), dict):
            stats_raw.update(row["stats"])
        else:
            # on prend les clés numériques “connues” si elles sont au niveau racine
            stats_raw.update(row)

        canon_stats = canonicalize_stats(stats_raw)

        return {
            "id": player_id,
            "name": name,
            "team": team,
            "team_id": team_id,
            "position": position,
            "league": league_name,
            "stats": canon_stats,
            "raw": row,
        }
