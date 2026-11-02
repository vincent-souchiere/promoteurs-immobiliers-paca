#import duckdb

#fichier = "data/raw/sirene/sirene_unites_legales.parquet"
#con = duckdb.connect() # Ouverture du fichier Parquet

 
#resultat = con.execute(
#    f"SELECT COUNT(*) AS nb_lignes FROM read_parquet('{fichier}')"
#).fetchone() # Lecture du fichier Parquet en retournant une seule ligne car le format est un tuple

#print(f"Nombre de lignes : {resultat[0]}") # Affichage du nombre de ligne

# Afficher les colonnes et leurs types
#colonnes = con.execute(
#    f"DESCRIBE SELECT * FROM read_parquet('{fichier}')"
#).fetchdf()

#print("\nStructure du fichier SIRENE :")
#print(colonnes)

# Vérifier les identifiants SIREN
#identifiants = con.execute(f"""
#    SELECT
#        COUNT(*) AS nombre_lignes,
#        COUNT(siren) AS lignes_avec_siren,
#        COUNT(DISTINCT siren) AS siren_distincts
#    FROM read_parquet('{fichier}')
#""").fetchdf()

#print("\nVérification des identifiants :")
#print(identifiants)

# Examiner les statuts administratifs
#statuts = con.execute(f"""
#    SELECT
#        etatAdministratifUniteLegale,
#        COUNT(*) AS nombre_lignes
#    FROM read_parquet('{fichier}')
#    GROUP BY etatAdministratifUniteLegale
#    ORDER BY nombre_lignes DESC
#""").fetchdf()

#print("\nRépartition des statuts administratifs :")
#print(statuts)

# Examiner les codes d'activité les plus fréquents
#activites = con.execute(f"""
#    SELECT
#        activitePrincipaleUniteLegale,
#        COUNT(*) AS nombre_entreprises
#    FROM read_parquet('{fichier}')
#    GROUP BY activitePrincipaleUniteLegale
#    ORDER BY nombre_entreprises DESC
#    LIMIT 20
#""").fetchdf()

#print("\nLes 20 codes d'activité les plus fréquents :")
#print(activites)



# ==========================================
# RECHERCHE DES PROMOTEURS POTENTIELS ACTIFS
# ==========================================

#codes_cibles = con.execute(f"""
#    SELECT
#        activitePrincipaleUniteLegale AS code_naf,
#        COUNT(*) AS nombre_entreprises_actives
#    FROM read_parquet('{fichier}')
#    WHERE activitePrincipaleUniteLegale IN (
#        '41.10A',
#        '41.10B',
#        '41.10C',
#        '41.10D',
#        '68.10Z'
#    )
#    AND etatAdministratifUniteLegale = 'A'
#    GROUP BY activitePrincipaleUniteLegale
#    ORDER BY nombre_entreprises_actives DESC
#""").fetchdf()

#print("\nEntreprises actives correspondant aux codes ciblés :")
#print(codes_cibles)



# ==========================================
# COMPARAISON DES STATUTS PAR CODE NAF
# ==========================================

#statuts_immobilier = con.execute(f"""
#    SELECT
#        activitePrincipaleUniteLegale AS code_naf,
#        etatAdministratifUniteLegale AS statut,
#        COUNT(*) AS nombre_entreprises
#    FROM read_parquet('{fichier}')
#    WHERE etatAdministratifUniteLegale = 'A' 
#        AND activitePrincipaleUniteLegale IN (
#            '41.10A',
#            '41.10B',
#            '41.10C',
#            '41.10D',
#            '68.10Z'
#        )
#    GROUP BY
#        activitePrincipaleUniteLegale,
#        etatAdministratifUniteLegale
#    ORDER BY
#        code_naf,
#        statut
#""").fetchdf()

#print("\nRépartition des entreprises par code NAF et statut :")
#print(statuts_immobilier)



# ==========================================
# CRÉATION D'UNE SÉLECTION D'ENTREPRISES ACTIVES
# ==========================================

#import duckdb

#fichier = "data/raw/sirene/sirene_unites_legales.parquet"

#con = duckdb.connect()

#entreprises_actives = con.execute(f"""
#    SELECT
#        siren,
#        denominationUniteLegale,
#        nomUniteLegale,
#        activitePrincipaleUniteLegale,
#        etatAdministratifUniteLegale
#    FROM read_parquet('{fichier}')
#    WHERE etatAdministratifUniteLegale = 'A'
#      AND activitePrincipaleUniteLegale IN (
#          '41.10A',
#          '41.10B',
#          '41.10C',
#          '41.10D',
#          '68.10Z'
#      )
#""").fetchdf()

#entreprises_actives.to_parquet(
#    "data/processed/sirene/sirene_unites_legales_immobilier_actif.parquet",
#    index=False
#)

#print(f"Nombre d'entreprises extraites : {len(entreprises_actives)}")
#print("Export terminé.")

# con.close()


import duckdb

fichier = "data/raw/sirene_unites_legales.parquet"

con = duckdb.connect()

entreprises_actives = con.execute(f"""
    SELECT
        siren,
        denominationUniteLegale,
        nomUniteLegale,
        activitePrincipaleUniteLegale,
        etatAdministratifUniteLegale
    FROM read_parquet('{fichier}')
    WHERE etatAdministratifUniteLegale = 'A'
      AND activitePrincipaleUniteLegale IN (
          '41.10A',
          '41.10B',
          '41.10C',
          '41.10D',
          '68.10Z'
      )
""").fetchdf()

entreprises_actives.to_parquet(
    "data/processed/entreprises_immobilieres_actives.parquet",
    index=False
)

print(f"Nombre d'entreprises extraites : {len(entreprises_actives)}")
print("Export terminé.")

con.close()