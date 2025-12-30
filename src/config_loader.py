import json
from pathlib import Path
from typing import Dict, Any

DEFAULT_WEIGHTS = {
    "goal": 5.0,
    "assist": 3.0,
    "yellowCard": -1.0,
    "redCard": -3.0,
    "chancesCreated": 0.5,
    "bigChancesCreated": 1.0,
    "tackles": 0.1,
    "interceptions": 0.1,
    "recoveries": 0.1,
    "penaltyWon": 2.0,
    "possWonAtt3rd": 0.2,
    "bigChanceMissed": -1.0,
    "expectedGoals": 0.0,
    "expectedAssists": 0.0,
}

def load_weights(path: str = "config/scoring.v1.json") -> Dict[str, float]:
    p = Path(path)
    if not p.exists():
        return DEFAULT_WEIGHTS

    data: Dict[str, Any] = json.loads(p.read_text(encoding="utf-8"))
    w = data.get("weights", {})
    # Merge + cast float, avec fallback propre
    merged = dict(DEFAULT_WEIGHTS)
    for k, v in w.items():
        try:
            merged[k] = float(v)
        except Exception:
            pass
    return merged
