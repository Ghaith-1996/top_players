from mobfot import MobFot
import json

client = MobFot()
try:
    # Haaland
    pid = 737066
    p_data = client.get_player(pid)
    print("Keys:", p_data.keys())
    if "stats" in p_data:
        print("Stats Keys:", p_data["stats"].keys())
except Exception as e:
    print("Error:", e)
