from typing import Dict, List, Set, Any, Tuple
from mobfot import MobFot
from src.config import WEIGHTS, INTERNATIONAL_CUPS

class BonusService:
    def __init__(self, client: MobFot):
        self._client = client
        self._top4_cache: Dict[int, Set[int]] = {}

    def get_top4_teams(self, league_id: int) -> Set[int]:
        """Récupère les IDs des équipes dans le Top 4 d'une ligue."""
        if league_id in self._top4_cache:
            return self._top4_cache[league_id]
        
        try:
            data = self._client.get_league(league_id)
            table_data = data.get("table", [])
            if not table_data:
                return set()
            
            # Structure: table -> [ { 'data': { 'table': { 'all': [...] } } } ]
            table_rows = []
            if isinstance(table_data, list) and len(table_data) > 0:
                inner_data = table_data[0].get("data", {})
                table_rows = inner_data.get("table", {}).get("all", [])
            
            top4 = {int(row.get("id")) for row in table_rows[:4] if row.get("id")}
            self._top4_cache[league_id] = top4
            return top4
        except Exception as e:
            print(f"DEBUG: Error fetching top 4: {e}")
            return set()

    def calculate_player_bonuses(self, player_id: int, top4_ids: Set[int], season: str = "2024/2025") -> Tuple[float, Dict[str, float]]:
        """
        Calcule les bonus pour UN joueur en analysant ses matchs récents.
        """
        bonus_score = 0.0
        breakdown = {
            "bonusGoalTop4": 0.0,
            "bonusAssistTop4": 0.0,
            "bonusUclQF": 0.0,
            "bonusUclSF": 0.0,
            "bonusUclFinal": 0.0,
            "bonusMotm": 0.0
        }

        try:
            # get_player renvoie les stats détaillées
            data = self._client.get_player(player_id)
            # On cherche les matchs de la saison
            matches = data.get("recentMatches", []) # Parfois sous 'recentMatches' ou 'stats'
            
            for m in matches:
                # On vérifie si c'est un but ou assist
                goals = int(m.get("goals", 0) or 0)
                assists = int(m.get("assists", 0) or 0)
                is_motm = bool(m.get("playerOfTheMatch", False))
                
                if goals == 0 and assists == 0 and not is_motm:
                    continue

                if is_motm:
                    val = WEIGHTS.bonusMotm
                    bonus_score += val
                    breakdown["bonusMotm"] += val

                opp_raw = m.get("opponentTeamId")
                if opp_raw is None: continue
                opponent_id = int(opp_raw)
                m_league_id = m.get("leagueId")
                # Certains champs peuvent être dans 'stage' ou 'roundName'
                stage_name = str(m.get("stage") or m.get("roundName") or "").lower()

                # 1. Bonus Top 4 (Ligue Domestique)
                if opponent_id in top4_ids:
                    if goals > 0:
                        val = goals * WEIGHTS.bonusGoalTop4
                        bonus_score += val
                        breakdown["bonusGoalTop4"] += val
                    if assists > 0:
                        val = assists * WEIGHTS.bonusAssistTop4
                        bonus_score += val
                        breakdown["bonusAssistTop4"] += val

                # 2. Bonus Compétitions Internationales (Stages)
                if m_league_id in INTERNATIONAL_CUPS:
                    # Quart de finale
                    if "quarter" in stage_name or "1/4" in stage_name:
                        if goals > 0:
                            val = goals * WEIGHTS.bonusGoalUclQF
                            bonus_score += val
                            breakdown["bonusUclQF"] += val
                        if assists > 0:
                            val = assists * WEIGHTS.bonusAssistUclQF
                            bonus_score += val
                            breakdown["bonusUclQF"] += val
                    # Demi-finale
                    elif "semi" in stage_name or "1/2" in stage_name:
                        if goals > 0:
                            val = goals * WEIGHTS.bonusGoalUclSF
                            bonus_score += val
                            breakdown["bonusUclSF"] += val
                        if assists > 0:
                            val = assists * WEIGHTS.bonusAssistUclSF
                            bonus_score += val
                            breakdown["bonusUclSF"] += val
                    # Finale
                    elif "final" in stage_name and "semi" not in stage_name and "quarter" not in stage_name:
                        if goals > 0:
                            val = goals * WEIGHTS.bonusGoalUclFinal
                            bonus_score += val
                            breakdown["bonusUclFinal"] += val
                        if assists > 0:
                            val = assists * WEIGHTS.bonusAssistUclFinal
                            bonus_score += val
                            breakdown["bonusUclFinal"] += val

            return float(round(bonus_score, 2)), breakdown
        except Exception as e:
            print(f"DEBUG: Error calculating bonuses for player {player_id}: {e}")
            return 0.0, breakdown
