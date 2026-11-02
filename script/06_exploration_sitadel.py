#import duckdb

#fichier = "data/raw/sitadel/sitadel_autorisations_logements_2026_09.csv"

#con = duckdb.connect()

#colonnes = con.execute(f"""
#    DESCRIBE
#    SELECT *
#    FROM read_csv(
#        '{fichier}',
#        delim=';',
#        header=true,
#        all_varchar=true
#    )
#""").fetchdf()

#print("\n=== COLONNES DE SITADEL ===\n")

#print(colonnes[["column_name", "column_type"]].to_string(index=False))

#con.close()

# 




#import duckdb

#fichier = "data/raw/sitadel/sitadel_autorisations_logements_2026_09.csv"

#con = duckdb.connect()

# Lire le fichier SITADEL
#source = f"""
#    read_csv(
#        '{fichier}',
#        delim=';',
#        header=true,
#        all_varchar=true,
#        sample_size=-1
#    )
#"""

# 1. Nombre total de lignes
#nombre_lignes = con.execute(f"""
#    SELECT COUNT(*)
#    FROM {source}
#""").fetchone()[0]

#print("Nombre total de lignes :", nombre_lignes)

#con.close()


# 

#import duckdb

#fichier = "data/raw/sitadel/sitadel_autorisations_logements_2026_09.csv"

#con = duckdb.connect()

# Lire le fichier SITADEL
#source = f"""
#    read_csv(
#        '{fichier}',
#        delim=';',
#        header=true,
#        all_varchar=true,
#        sample_size=-1
#    )
#"""

# 1. Nombre total de lignes
#nombre_lignes = con.execute(f"""
#    SELECT COUNT(*)
#    FROM {source}
#""").fetchone()[0]

#print("Nombre total de lignes :", nombre_lignes)

# 2. Nombre de lignes par département
#exemple = con.execute(f"""
#    SELECT
#        DEP_CODE,
#        DEP_LIBELLE,
#        COMM,
#        TYPE_DAU,
#        NUM_DAU,
#        ETAT_DAU,
#        DATE_REELLE_AUTORISATION,
#        DENOM_DEM,
#        SIREN_DEM,
#        SIRET_DEM,
#        SEC_CADASTRE1,
#        NUM_CADASTRE1,
#        NB_LGT_TOT_CREES
#    FROM {source}
#    WHERE DEP_CODE IN ('04', '05', '06', '13', '83', '84')
#    LIMIT 10
#""").fetchdf()

#print(exemple.to_string(index=False))

#print("\n=== RÉPARTITION PAR DÉPARTEMENT ===")
#print(departements.to_string(index=False))

#con.close

import duckdb
from pathlib import Path

# Chemins des fichiers
fichier_source = "data/raw/sitadel/sitadel_autorisations_logements_2026_09.csv"
fichier_sortie = "data/processed/sitadel/sitadel_autorisations_logements_paca.parquet"

# Créer le dossier de sortie
#Path("data/processed/sitadel").mkdir(parents=True, exist_ok=True)

con = duckdb.connect()

# Préparer les données SITADEL de PACA
con.execute(f"""
    COPY (
        SELECT
            DEP_CODE AS code_departement,
            DEP_LIBELLE AS departement,
            COMM AS code_commune,
            TYPE_DAU AS type_autorisation,
            NUM_DAU AS numero_dossier,
            ETAT_DAU AS etat_dossier,
            DATE_REELLE_AUTORISATION AS date_autorisation,
            DATE_REELLE_DOC AS date_debut_travaux,
            DATE_REELLE_DAACT AS date_achevement,
            DENOM_DEM AS nom_demandeur,
            SIREN_DEM AS siren_demandeur,
            SIRET_DEM AS siret_demandeur,
            ADR_LOCALITE_TER AS commune_projet,
            ADR_CODPOST_TER AS code_postal_projet,
            ADR_NUM_TER AS numero_voie_projet,
            ADR_LIBVOIE_TER AS voie_projet,
            SEC_CADASTRE1 AS section_cadastrale_1,
            NUM_CADASTRE1 AS parcelle_cadastrale_1,
            SEC_CADASTRE2 AS section_cadastrale_2,
            NUM_CADASTRE2 AS parcelle_cadastrale_2,
            SEC_CADASTRE3 AS section_cadastrale_3,
            NUM_CADASTRE3 AS parcelle_cadastrale_3,
            SUPERFICIE_TERRAIN AS superficie_terrain,
            NATURE_PROJET_DECLAREE AS nature_projet_declaree,
            NATURE_PROJET_COMPLETEE AS nature_projet_completee,
            NB_LGT_TOT_CREES AS logements_crees,
            NB_LGT_IND_CREES AS logements_individuels_crees,
            NB_LGT_COL_CREES AS logements_collectifs_crees,
            NB_LGT_DEMOLIS AS logements_demolis,
            SURF_HAB_CREEE AS surface_habitable_creee
        FROM read_csv(
            '{fichier_source}',
            delim=';',
            header=true,
            all_varchar=true,
            sample_size=-1
        )
        WHERE DEP_CODE IN ('04', '05', '06', '13', '83', '84')
    )
    TO '{fichier_sortie}'
    (FORMAT PARQUET)
""")

print("Fichier SITADEL PACA créé :", fichier_sortie)

# Vérifier le résultat
verification = con.execute(f"""
    SELECT
        COUNT(*) AS nombre_lignes,
        COUNT(DISTINCT numero_dossier) AS dossiers_distincts,
        COUNT(siren_demandeur) AS siren_renseignes,
        COUNT(siret_demandeur) AS siret_renseignes
    FROM read_parquet('{fichier_sortie}')
""").fetchdf()

print("\n=== VÉRIFICATION ===")
print(verification.to_string(index=False))

con.close()