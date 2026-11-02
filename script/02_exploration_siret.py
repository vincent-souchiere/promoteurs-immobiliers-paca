#import duckdb

#fichier = "data/raw/sirene/sirene_etablissements.parquet"

#con = duckdb.connect()

# Compter les établissements par département en PACA
#regionpaca = con.execute(f"""
#    SELECT
#        SUBSTRING(codePostalEtablissement, 1, 2) AS departement,
#        COUNT(*) AS nombre_etablissements
#    FROM read_parquet('{fichier}')
#    WHERE codePostalEtablissement IS NOT NULL
#      AND codePostalEtablissement <> '[ND]'
#      AND SUBSTRING(codePostalEtablissement, 1, 2)
#          IN ('04', '05', '06', '13', '83', '84')
#      AND etatAdministratifEtablissement = 'A'
#    GROUP BY departement
#    ORDER BY departement ASC
#""").fetchdf()

#print("Établissements par département en PACA :")
#print(regionpaca.to_string(index=False))

#con.close()


# Compter les établissements par code postal
# resultat = con.execute(f"""
#     SELECT
#         codePostalEtablissement,
#         COUNT(*) AS nombre_etablissements
#    FROM read_parquet('{fichier}')
#    WHERE codePostalEtablissement IS NOT NULL
#    GROUP BY codePostalEtablissement
#    ORDER BY nombre_etablissements DESC
#    LIMIT 20
#""").fetchdf()

#print("\nLes 20 codes postaux les plus fréquents :")
#print(resultat.to_string(index=False))

#con.close()

import duckdb

fichier_source = "data/raw/sirene/sirene_etablissements.parquet"
fichier_sortie = "data/processed/sirene/sirene_etablissements_actifs_paca.parquet"

con = duckdb.connect()

requete = f"""
    COPY (
        SELECT
            siren,
            nic,
            siret,
            dateCreationEtablissement,
            etablissementSiege,
            activitePrincipaleEtablissement,
            nomenclatureActivitePrincipaleEtablissement,
            activitePrincipaleNAF25Etablissement,
            codePostalEtablissement,
            codeCommuneEtablissement,
            libelleCommuneEtablissement,
            numeroVoieEtablissement,
            typeVoieEtablissement,
            libelleVoieEtablissement,
            etatAdministratifEtablissement
        FROM read_parquet('{fichier_source}')
        WHERE codePostalEtablissement IS NOT NULL
          AND codePostalEtablissement <> '[ND]'
          AND SUBSTRING(codePostalEtablissement, 1, 2)
              IN ('04', '05', '06', '13', '83', '84')
          AND etatAdministratifEtablissement = 'A'
    )
    TO '{fichier_sortie}'
    (FORMAT PARQUET)
"""

con.execute(requete)

# On compte le nombre de ligne avec fetchdf

verification = con.execute(f"""
    SELECT COUNT(*) AS nombre_etablissements
    FROM read_parquet('{fichier_sortie}')
""").fetchdf()

print("Export terminé !")
print(verification.to_string(index=False))

con.close()