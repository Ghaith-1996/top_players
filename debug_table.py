from mobfot import MobFot
import json

client = MobFot()
try:
    # Premier League
    data = client.get_league(47)
    if "table" in data:
        t = data["table"]
        if isinstance(t, list) and len(t) > 0:
            print("Table[0] Keys:", t[0].keys())
            if "data" in t[0]:
                print("Table[0]['data'] Keys:", t[0]["data"].keys())
                if "table" in t[0]["data"]:
                     print("Table[0]['data']['table'] Keys:", t[0]["data"]["table"].keys())
                     if "all" in t[0]["data"]["table"]:
                          print("Top Team ID:", t[0]["data"]["table"]["all"][0].get("id"))
except Exception as e:
    print("Error:", e)
