from config import engine

def test_connection():
    try:
        # Vérifie si la connexion à la base de données est possible
        with engine.connect() as connection:
            print("Connexion à la base de données réussie !")
    except Exception as e:
        print(f"Erreur lors de la connexion à la base de données : {e}")

def list_tables():
    try:
        # Liste les tables existantes dans la base de données
        with engine.connect() as connection:
            result = connection.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in result]
            print("Tables existantes :", tables)
    except Exception as e:
        print(f"Erreur lors de la récupération des tables : {e}")

if __name__ == "__main__":
    test_connection()
    list_tables()