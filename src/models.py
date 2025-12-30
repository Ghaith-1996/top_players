from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class CanonicalStats(BaseModel):
    minutes: int = 0
    goal: int = 0
    assist: int = 0
    yellowCard: int = 0
    redCard: int = 0
    chancesCreated: int = 0
    bigChancesCreated: int = 0
    tackles: int = 0
    interceptions: int = 0
    recoveries: int = 0
    penaltyWon: int = 0
    possWonAtt3rd: int = 0
    bigChanceMissed: int = 0
    expectedGoals: int = 0
    expectedAssists: int = 0

class PlayerOut(BaseModel):
    id: int
    name: str
    team: Optional[str] = None
    league: Optional[str] = None
    position: Optional[str] = None
    stats: CanonicalStats
    score: float
    breakdown: Dict[str, float] = Field(default_factory=dict)
    raw: Dict[str, Any] = Field(default_factory=dict)  # utile pour debug (à retirer plus tard)
