from src.database import engine
from src.db_models import Base

if __name__ == "__main__":
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")
