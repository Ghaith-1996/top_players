from src.database import SessionLocal
from src.db_models import PlayerStats

db = SessionLocal()
seasons = ["2024/2025", "2023/2024", "2022/2023"]

print("--- Data Count by Season ---")
for s in seasons:
    count = db.query(PlayerStats).filter(PlayerStats.season == s).count()
    print(f"Season {s}: {count} records")

db.close()
