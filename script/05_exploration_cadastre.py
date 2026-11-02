# 1. APERCU

#import duckdb

#fichier = "data/raw/cadastre/cadastre-source.parquet"

#con = duckdb.connect()


#fichier = con.execute(f"""
#    DESCRIBE
#    SELECT *
#    FROM read_parquet('{fichier}')
#""").fetchdf()

#print("\n=== COLONNES DU CADASTRE ===\n")
#print(fichier[["column_name", "column_type"]].to_string(index=False))

#con.close

# ------- 2. Afficher les 5 premières lignes

#import duckdb

#fichier = "data/raw/cadastre/cadastre-source.parquet"

#con = duckdb.connect()

#apercu = con.execute(f"""
#    SELECT *
#    FROM read_parquet('{fichier}')
#    LIMIT 5
#""").fetchdf()

#print("\n=== APERÇU DES DONNÉES ===\n")
#print(apercu.to_string(index=False))

#con.close


# 4. Identifier les différents types d'objets cadastraux par dpt

#import duckdb

#types_objets = "data/raw/cadastre/cadastre-source.parquet"

#con = duckdb.connect()


#types_objets = con.execute(f"""
#    SELECT
#        type_objet,
#        COUNT(*) AS nombre_lignes,
#        departement
#    FROM read_parquet('{types_objets}')
#    WHERE SUBSTRING(departement, 1, 2)
#            IN ('04', '05', '06', '13', '83', '84')
#    GROUP BY type_objet, departement
#    ORDER BY nombre_lignes DESC
#""").fetchdf()

#print("\n=== TYPES D'OBJETS CADASTRAUX ===\n")
#print(types_objets.to_string(index=False))

#con.close

import duckdb
from pathlib import Path

# Chemins des fichiers
fichier_source = "data/raw/cadastre/cadastre-source.parquet"
fichier_sortie = "data/processed/cadastre/parcelles_paca.parquet"

# Connexion DuckDB
con = duckdb.connect()

# Préparer les parcelles cadastrales de PACA
requete = f"""
    COPY (
        SELECT
            id AS id_parcelle,
            departement,
            commune,
            prefixe,
            section,
            parcelle,
            contenance,
            millesime,
            geom_srid,
            geometry
        FROM read_parquet('{fichier_source}')
        WHERE type_objet = 'parcelles'
          AND departement IN ('04', '05', '06', '13', '83', '84')
    )
    TO '{fichier_sortie}'
    (FORMAT PARQUET)
"""

con.execute(requete)

print("Préparation du cadastre terminée.")
print("Fichier créé :", fichier_sortie)

# Vérifier le résultat
verification = con.execute(f"""
    SELECT
        COUNT(*) AS nombre_lignes,
        COUNT(id_parcelle) AS identifiants_renseignes,
        COUNT(DISTINCT id_parcelle) AS identifiants_distincts
    FROM read_parquet('{fichier_sortie}')
""").fetchdf()

print("\n=== VÉRIFICATION ===")
print(verification.to_string(index=False))

con.close()