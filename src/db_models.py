from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, UniqueConstraint, Date
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class League(Base):
    __tablename__ = "leagues"
    league_id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    country = Column(String(100))
    
    teams = relationship("Team", back_populates="league")

class Team(Base):
    __tablename__ = "teams"
    team_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.league_id"))
    
    league = relationship("League", back_populates="teams")
    players = relationship("Player", back_populates="team")

class Player(Base):
    __tablename__ = "players"
    player_id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.team_id"))
    position = Column(String(100))
    nationality = Column(String(100))
    
    team = relationship("Team", back_populates="players")
    stats = relationship("PlayerStats", back_populates="player")
    matches = relationship("PlayerMatch", back_populates="player")

class PlayerStats(Base):
    __tablename__ = "player_stats"
    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("players.player_id"), nullable=False)
    competition_id = Column(Integer, ForeignKey("leagues.league_id"), nullable=False)
    season = Column(String(50), nullable=False)
    
    # Canonical Stats
    minutes = Column(Integer, default=0)
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    yellow_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)
    chances_created = Column(Integer, default=0)
    big_chances_created = Column(Integer, default=0)
    tackles = Column(Integer, default=0)
    interceptions = Column(Integer, default=0)
    recoveries = Column(Integer, default=0)
    penalty_won = Column(Integer, default=0)
    poss_won_att_3rd = Column(Integer, default=0)
    big_chance_missed = Column(Integer, default=0)
    expected_goals = Column(Float, default=0.0)
    expected_assists = Column(Float, default=0.0)
    
    # Calculated Scores
    base_score = Column(Float, default=0.0)
    bonus_goal_top4 = Column(Float, default=0.0)
    bonus_assist_top4 = Column(Float, default=0.0)
    bonus_ucl_qf = Column(Float, default=0.0)
    bonus_ucl_sf = Column(Float, default=0.0)
    bonus_ucl_final = Column(Float, default=0.0)
    bonus_motm = Column(Float, default=0.0)
    total_score = Column(Float, default=0.0)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    player = relationship("Player", back_populates="stats")
    
    __table_args__ = (UniqueConstraint('player_id', 'competition_id', 'season', name='_player_comp_season_uc'),)

class PlayerMatch(Base):
    __tablename__ = "player_matches"
    match_id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.player_id"), nullable=False)
    competition_id = Column(Integer, ForeignKey("leagues.league_id"))
    opponent_team_id = Column(Integer, ForeignKey("teams.team_id"))
    season = Column(String(50))
    match_date = Column(Date)
    
    minutes_played = Column(Integer, default=0)
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    is_motm = Column(Boolean, default=False)
    yellow_card = Column(Boolean, default=False)
    red_card = Column(Boolean, default=False)
    rating = Column(Float)
    round_name = Column(String(255))
    
    player = relationship("Player", back_populates="matches")
    
    __table_args__ = (UniqueConstraint('match_id', 'player_id', name='_match_player_uc'),)
