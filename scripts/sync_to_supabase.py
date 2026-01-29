import sys
import os
from sqlalchemy.orm import Session

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import SessionLocal, engine
from src.db_models import Player, PlayerStats, Team, League, Base
from src.logic.fotmob_service import FotmobService
from src.logic.bonus_service import BonusService
from src.logic.scoring_service import compute_score
from src.config import LEAGUE_TO_CUPS, INTERNATIONAL_CUPS

def sync_data():
    db: Session = SessionLocal()
    fotmob = FotmobService()
    bonus_service = BonusService(fotmob._client)
    
    # TOP 5 LEAGUES
    LEAGUES = {
        47: "Premier League",
        87: "La Liga",
        54: "Bundesliga",
        55: "Serie A",
        53: "Ligue 1"
    }
    
    SEASONS = [
        "2024/2025",
        "2023/2024",
        "2022/2023"
    ]
    
    try:
        for season in SEASONS:
            print(f"\n=== Syncing Season {season} ===")
            for league_id, league_name in LEAGUES.items():
                print(f"--- Syncing {league_name} ---")
                
                # 1. Ensure League exists
                db_league = db.query(League).filter(League.league_id == league_id).first()
                if not db_league:
                    db_league = League(league_id=league_id, name=league_name)
                    db.add(db_league)
                    db.commit()

                # 2. Get Top 4 for bonuses
                top4_ids = bonus_service.get_top4_teams(league_id)
                
                # 3. Get all valid Team IDs for this league (to avoid pollution from Cup matches)
                print(f"  Fetching valid teams from League Table...")
                valid_team_ids = fotmob.get_league_team_ids(league_id, season=season)
                print(f"  Found {len(valid_team_ids)} valid teams.")

                # 4. Fetch players stats (League + Cups + International)
                cids = [league_id]
                if league_id in LEAGUE_TO_CUPS:
                    cids.extend(LEAGUE_TO_CUPS[league_id])
                cids.extend(INTERNATIONAL_CUPS)
                
                # Global stats for this league (Player ID -> Aggregated Stats Payload)
                players_data = {} 
                
                for cid in cids:
                    print(f"  Fetching competition {cid}...")
                    players_in_this_comp = {} 
                    
                    try:
                        rows = fotmob.fetch_league_players(cid, season=season)
                        if not rows:
                            continue
                            
                        for row in rows:
                            payload = fotmob.to_player_payload(row, league_name=league_name)
                            pid = payload["id"]
                            tid = payload.get("team_id")
                            if pid <= 0: continue
                            
                            # CRITICAL FIX REVISED: 
                            # If we have valid_team_ids, strictly enforce that the player belongs to one of those teams.
                            # We only skip if we HAVE a valid list of teams and the player is NOT in it.
                            # (If get_league_team_ids failed and returned empty, we might fallback or skip? 
                            # Logic: If valid_team_ids is empty, something is wrong, maybe better to accept all to avoid zero data, 
                            # or strict fail. Let's assume strict fail is safer for pollution, but risky for empty data.)
                            
                            if valid_team_ids and tid not in valid_team_ids:
                                # Skip player from other leagues (e.g. opponent in CL)
                                continue

                            new_stats = payload["stats"]
                            
                            if pid not in players_in_this_comp:
                                players_in_this_comp[pid] = payload
                            else:
                                # Dans la MÊME compétition, on prend le MAX (pour éviter les doublons Goals vs Assists)
                                existing_s = players_in_this_comp[pid]["stats"]
                                for field_name in new_stats.model_dump().keys():
                                    current_val = getattr(existing_s, field_name)
                                    fresh_val = getattr(new_stats, field_name)
                                    setattr(existing_s, field_name, max(current_val, fresh_val))
                        
                        # Maintenant on fusionne les stats de CETTE compétition dans le total global (addition)
                        for pid, p_payload in players_in_this_comp.items():
                            if pid not in players_data:
                                players_data[pid] = p_payload
                            else:
                                # Entre DEUX compétitions différentes (ex: PL et UCL), on ADDITIONNE
                                e_stats = players_data[pid]["stats"]
                                n_stats = p_payload["stats"]
                                for field_name in n_stats.model_dump().keys():
                                    setattr(e_stats, field_name, getattr(e_stats, field_name) + getattr(n_stats, field_name))
                                    
                    except Exception as e:
                        print(f"  Error fetching {cid}: {e}")

                # 5. Save/Update in DB (Top 100 per league to avoid hammering)
                sorted_players = sorted(players_data.values(), key=lambda x: x["stats"].goal + x["stats"].assist, reverse=True)[:100]
                
                for p_payload in sorted_players:
                    pid = p_payload["id"]
                    name = p_payload["name"]
                    team_name = p_payload.get("team")
                    
                    # Check Team
                    db_team = None
                    if team_name:
                        db_team = db.query(Team).filter(Team.name == team_name).first()
                        if not db_team:
                            db_team = Team(name=team_name, league_id=league_id)
                            db.add(db_team)
                            db.commit()
                            db.refresh(db_team)

                    # Check Player
                    db_player = db.query(Player).filter(Player.player_id == pid).first()
                    if not db_player:
                        db_player = Player(
                            player_id=pid,
                            name=name,
                            team_id=db_team.team_id if db_team else None,
                            position=p_payload.get("position")
                        )
                        db.add(db_player)
                        db.commit()

                    # Calculate Score & Bonuses
                    stats = p_payload["stats"]
                    base_score, breakdown = compute_score(stats)
                    
                    bonus_score, bonus_breakdown = bonus_service.calculate_player_bonuses(pid, top4_ids, season=season)
                    
                    # Update or Create Stats
                    db_stats = db.query(PlayerStats).filter(
                        PlayerStats.player_id == pid,
                        PlayerStats.competition_id == league_id,
                        PlayerStats.season == season
                    ).first()
                    
                    if not db_stats:
                        db_stats = PlayerStats(
                            player_id=pid,
                            competition_id=league_id,
                            season=season
                        )
                        db.add(db_stats)

                    # Map categories
                    db_stats.minutes = stats.minutes
                    db_stats.goals = stats.goal
                    db_stats.assists = stats.assist
                    db_stats.yellow_cards = stats.yellowCard
                    db_stats.red_cards = stats.redCard
                    db_stats.chances_created = stats.chancesCreated
                    db_stats.big_chances_created = stats.bigChancesCreated
                    db_stats.tackles = stats.tackles
                    db_stats.interceptions = stats.interceptions
                    db_stats.recoveries = stats.recoveries
                    db_stats.penalty_won = stats.penaltyWon
                    db_stats.poss_won_att_3rd = stats.possWonAtt3rd
                    db_stats.big_chance_missed = stats.bigChanceMissed
                    db_stats.expected_goals = stats.expectedGoals
                    db_stats.expected_assists = stats.expectedAssists
                    
                    db_stats.base_score = base_score
                    db_stats.bonus_goal_top4 = bonus_breakdown.get("bonusGoalTop4", 0)
                    db_stats.bonus_assist_top4 = bonus_breakdown.get("bonusAssistTop4", 0)
                    db_stats.bonus_ucl_qf = bonus_breakdown.get("bonusUclQF", 0)
                    db_stats.bonus_ucl_sf = bonus_breakdown.get("bonusUclSF", 0)
                    db_stats.bonus_ucl_final = bonus_breakdown.get("bonusUclFinal", 0)
                    db_stats.bonus_motm = bonus_breakdown.get("bonusMotm", 0)
                    db_stats.total_score = base_score + bonus_score
                    
                    db.commit()
                    print(f"    Synced {name} ({season}) - Score: {db_stats.total_score:.2f}")

    except Exception as e:
        print(f"Global Sync Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    sync_data()
