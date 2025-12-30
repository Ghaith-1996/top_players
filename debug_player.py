from mobfot import MobFot
import json

client = MobFot()
try:
    # Get Premier League players
    data = client.get_league(47)
    # The stats are usually in data['stats']['players']
    players = data.get('stats', {}).get('players', [])
    if players:
        # Get first player from first category
        first_cat = players[0]
        p_list = first_cat.get('topThree', []) or first_cat.get('players', [])
        if p_list:
            p = p_list[0]
            pid = p.get('id')
            print(f"Found Player: {p.get('name')} ID: {pid}")
            
            p_data = client.get_player(pid)
            if p_data:
                print("Player Data Keys:", p_data.keys())
                if "recentMatches" in p_data:
                     print("Match sample:", json.dumps(p_data["recentMatches"][0], indent=2))
            else:
                print("Could not get player data for ID", pid)
except Exception as e:
    print("Error:", e)
