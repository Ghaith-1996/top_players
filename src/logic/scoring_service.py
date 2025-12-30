from typing import Dict, Tuple
from src.models import CanonicalStats
from src.config_loader import load_weights

WEIGHTS = load_weights()

def compute_score(stats: CanonicalStats) -> Tuple[float, Dict[str, float]]:
    breakdown: Dict[str, float] = {}

    def add(key: str, value: float) -> None:
        breakdown[key] = value * WEIGHTS[key]

    add("goal", stats.goal)
    add("assist", stats.assist)
    add("yellowCard", stats.yellowCard)
    add("redCard", stats.redCard)
    add("chancesCreated", stats.chancesCreated)
    add("bigChancesCreated", stats.bigChancesCreated)
    add("tackles", stats.tackles)
    add("interceptions", stats.interceptions)
    add("recoveries", stats.recoveries)
    add("penaltyWon", stats.penaltyWon)
    add("possWonAtt3rd", stats.possWonAtt3rd)
    add("bigChanceMissed", stats.bigChanceMissed)
    add("expectedGoals", stats.expectedGoals)
    add("expectedAssists", stats.expectedAssists)

    total = sum(breakdown.values())
    return float(round(total, 4)), {k: float(round(v, 4)) for k, v in breakdown.items()}
