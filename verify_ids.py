from mobfot import MobFot
import json

client = MobFot()

competitions = {
    "FA Cup": 132,
    "EFL Cup": 133,
    "Champions League": 42,
    "Europa League": 73,
    "Conference League": 9161,
    "Copa del Rey": 135,
    "Supercopa": 136,
    "Coppa Italia": 137,
    "Supercoppa": 138,
    "DFB Pokal": 139,
    "DFL Supercup": 140,
    "Coupe de France": 141,
    "Trophée des Champions": 142,
    "UEFA Super Cup": 77
}

results = {}
for name, cid in competitions.items():
    try:
        data = client.get_league(cid)
        # Check if it has stats
        has_stats = "stats" in data
        results[name] = {"id": cid, "valid": True, "has_stats": has_stats}
    except Exception as e:
        results[name] = {"id": cid, "valid": False, "error": str(e)}

print(json.dumps(results, indent=2))
