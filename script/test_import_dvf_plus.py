import duckdb

fichier_source = "data/raw/dvf_plus/dvf_plus_source_2026_02.csv"

con = duckdb.connect()

requete = f"""
    SELECT
        LPAD(TRIM(coddep), 2, '0') AS departement,
        COUNT(*) AS nombre_lignes
    FROM read_csv(
        '{fichier_source}',
        delim='|',
        header=true,
        all_varchar=true,
        sample_size=-1
    )
    WHERE LPAD(TRIM(coddep), 2, '0')
        IN ('04', '05', '06', '13', '83', '84')
    GROUP BY LPAD(TRIM(coddep), 2, '0')
    ORDER BY departement
"""

resultat = con.execute(requete).fetchdf()
print(resultat.to_string(index=False))

con.close()