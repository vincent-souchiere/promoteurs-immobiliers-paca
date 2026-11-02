#import duckdb
#import pandas as pd

#fichier = "data/raw/dvf/dvf_valeurs_foncieres_2026_s1.txt"

#con = duckdb.connect()


#departements = con.execute(f"""
#    SELECT
#        "Code departement" AS departement,
#        COUNT(*) AS nombre_lignes
#    FROM read_csv(
#        '{fichier}',
#        delim='|',
#        header=true,
#        all_varchar=true,
#        sample_size=-1
#    )
#    WHERE SUBSTRING("Code departement", 1, 2)
#                  IN ('04', '05', '06', '13', '83', '84')
#    GROUP BY "Code departement"
#    ORDER BY nombre_lignes DESC
#""").fetchdf()

#print("\nNombre de lignes par département :\n")
#print(departements.to_string(index=False))


#con.close()


import duckdb

fichier_source = "data/raw/dvf/dvf_valeurs_foncieres_2026_s1.txt"

fichier_sortie = (
    "data/processed/dvf/"
    "dvf_transactions_paca_2026_s1.parquet"
)

con = duckdb.connect()

requete = f"""
    COPY (
        SELECT
            "Identifiant de document",
            "No disposition",
            "Date mutation",
            "Nature mutation",
            "Valeur fonciere",
            "Code departement",
            "Code commune",
            "Commune",
            "Prefixe de section",
            "Section",
            "No plan",
            "Nombre de lots",
            "Code type local",
            "Type local",
            "Surface reelle bati",
            "Nombre pieces principales",
            "Nature culture",
            "Nature culture speciale",
            "Surface terrain"
        FROM read_csv(
            '{fichier_source}',
            delim='|',
            header=true,
            all_varchar=true,
            sample_size=-1
        )
        WHERE "Code departement" IN ('04', '05', '06', '13', '83', '84')
    )
    TO '{fichier_sortie}'
    (FORMAT PARQUET)
"""

con.execute(requete)

print("Export DVF PACA terminé !")
print(f"Fichier créé : {fichier_sortie}")

con.close()