from dataclasses import dataclass

@dataclass(frozen=True)
class ScoringWeights:
    goal: float = 5.0
    assist: float = 3.0
    yellowCard: float = -1.0
    redCard: float = -3.0
    chancesCreated: float = 0.5
    bigChancesCreated: float = 1.0
    tackles: float = 0.1
    interceptions: float = 0.1
    recoveries: float = 0.1
    penaltyWon: float = 2.0
    possWonAtt3rd: float = 0.2
    bigChanceMissed: float = -1.0
    expectedGoals: float = 0.0
    expectedAssists: float = 0.0

WEIGHTS = ScoringWeights()

# Cache TTL (secondes)
DEFAULT_CACHE_TTL_S = 15 * 60

# Filtre anti “small sample”
DEFAULT_MIN_MINUTES = 0
DEFAULT_LIMIT = 50
