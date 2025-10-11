from config import engine
from sqlalchemy.sql import text

def list_tables():
    """
    Liste les tables existantes dans la base de données.
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [row[0] for row in result]
            print("Tables existantes :", tables)
    except Exception as e:
        print(f"Erreur lors de la récupération des tables : {e}")

if __name__ == "__main__":
    list_tables()