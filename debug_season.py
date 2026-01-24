from mobfot import MobFot
import json

client = MobFot()
league_id = 47 # Premier League
season = "2023/2024"

print(f"Fetching PL for {season}...")
try:
    data = client.get_league(league_id, season=season)
    # Print top level keys
    print("Keys:", data.keys())
    
    # Check if stats exist
    if "stats" in data:
        print("Stats found.")
        stats = data["stats"]
        if "players" in stats:
             print(f"Players categories found: {len(stats['players'])}")
             # Print first category name
             print("First category:", stats['players'][0].get("name"))
        else:
             print("Key 'players' NOT in stats.")
    else:
        print("Key 'stats' NOT in data.")
        
    # Check 'table' just in case
    # if "table" in data:
    #    print("Table found.")
        
except Exception as e:
    print(f"Error: {e}")
