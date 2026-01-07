-- Schema for Top Players Project
-- This schema supports both PostgreSQL and SQLite

-- 1. Leagues Reference
CREATE TABLE IF NOT EXISTS leagues (
    league_id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    country VARCHAR(100)
);

-- 2. Teams Reference
CREATE TABLE IF NOT EXISTS teams (
    team_id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    league_id INTEGER REFERENCES leagues(league_id)
);

-- 3. Players Reference
CREATE TABLE IF NOT EXISTS players (
    player_id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    team_id INTEGER REFERENCES teams(team_id),
    position VARCHAR(100),
    nationality VARCHAR(100)
);

-- 4. Player Aggregated Stats (Season/Competition level)
-- Stores the 'CanonicalStats' used for scoring
CREATE TABLE IF NOT EXISTS player_stats (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(player_id),
    competition_id INTEGER NOT NULL REFERENCES leagues(league_id),
    season VARCHAR(50) NOT NULL, -- e.g., "2024/2025"
    
    -- Canonical Stats (Matches src/models.py)
    minutes INTEGER DEFAULT 0,
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0,
    chances_created INTEGER DEFAULT 0,
    big_chances_created INTEGER DEFAULT 0,
    tackles INTEGER DEFAULT 0,
    interceptions INTEGER DEFAULT 0,
    recoveries INTEGER DEFAULT 0,
    penalty_won INTEGER DEFAULT 0,
    poss_won_att_3rd INTEGER DEFAULT 0,
    big_chance_missed INTEGER DEFAULT 0,
    expected_goals FLOAT DEFAULT 0.0,
    expected_assists FLOAT DEFAULT 0.0,
    
    -- Calculated Scores & Bonuses (Matches src/logic/bonus_service.py)
    base_score FLOAT DEFAULT 0.0, -- Score before bonuses
    bonus_goal_top4 FLOAT DEFAULT 0.0,
    bonus_assist_top4 FLOAT DEFAULT 0.0,
    bonus_ucl_qf FLOAT DEFAULT 0.0,
    bonus_ucl_sf FLOAT DEFAULT 0.0,
    bonus_ucl_final FLOAT DEFAULT 0.0,
    bonus_motm FLOAT DEFAULT 0.0,
    
    total_score FLOAT DEFAULT 0.0,
    
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, competition_id, season)
);

-- 5. Player Matches (Match-level detail)
-- Crucial for recalculating bonuses if weights change
CREATE TABLE IF NOT EXISTS player_matches (
    match_id INTEGER PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(player_id),
    competition_id INTEGER REFERENCES leagues(league_id),
    opponent_team_id INTEGER REFERENCES teams(team_id),
    season VARCHAR(50),
    match_date DATE,
    
    minutes_played INTEGER DEFAULT 0,
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    is_motm BOOLEAN DEFAULT FALSE,
    yellow_card BOOLEAN DEFAULT FALSE,
    red_card BOOLEAN DEFAULT FALSE,
    rating FLOAT,
    round_name VARCHAR(255), -- e.g., "Quarter-final", "Semi-final"
    
    UNIQUE(match_id, player_id)
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_player_stats_player_id ON player_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_season ON player_stats(season);
CREATE INDEX IF NOT EXISTS idx_player_stats_score ON player_stats(total_score DESC);
CREATE INDEX IF NOT EXISTS idx_player_matches_player_id ON player_matches(player_id);
