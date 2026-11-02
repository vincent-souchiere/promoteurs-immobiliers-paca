import psycopg

from db_config import DB_CONFIG


try:
    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")

            version = cur.fetchone()[0]

            print("Connexion réussie !")
            print(version)

except Exception as e:
    print("Erreur de connexion :")
    print(e)