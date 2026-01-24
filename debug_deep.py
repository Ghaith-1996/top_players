from mobfot import MobFot
import requests
import json

client = MobFot()
league_id = 47 # Premier League
season = "2023/2024"

print(f"Fetching PL for {season}...")
data = client.get_league(league_id, season=season)
stats = data.get("stats")
if stats and "players" in stats:
    first_cat = stats["players"][0]
    print(f"Category: {first_cat.get('name')}")
    url = first_cat.get("fetchAllUrl")
    print(f"Fetch URL: {url}")
    
    if url:
        print("Fetching detailed list...")
        res = requests.get(url)
        print(f"Status: {res.status_code}")
        # print excerpt
        try:
            js = res.json()
            print("Keys:", js.keys())
            if "TopLists" in js:
                print("TopLists count:", len(js["TopLists"]))
        except:
            print("Not JSON")
else:
    print("No stats players found")
