from pathlib import Path

import duckdb


# ============================================================
# CONFIGURATION
# ============================================================

RACINE_PROJET = Path(__file__).resolve().parent.parent

FICHIER_SOURCE = (
    RACINE_PROJET
    / "data"
    / "raw"
    / "dvf_plus"
    / "dvf_plus_source_2026_02.csv"
)

FICHIER_PARQUET = (
    RACINE_PROJET
    / "data"
    / "processed"
    / "dvf"
    / "dvf_plus_paca_2026_02.parquet"
)

DEPARTEMENTS_PACA = ("04", "05", "06", "13", "83", "84")


# ============================================================
# EXPLORATION DU CSV SOURCE
# ============================================================

def explorer_csv(con):
    print("\n" + "=" * 60)
    print("1. EXPLORATION DU CSV SOURCE")
    print("=" * 60)

    if not FICHIER_SOURCE.exists():
        raise FileNotFoundError(
            f"Fichier source introuvable : {FICHIER_SOURCE}"
        )

    chemin_csv = FICHIER_SOURCE.as_posix().replace("'", "''")

    requete = f"""
        SELECT
            LPAD(TRIM(coddep), 2, '0') AS departement,
            COUNT(*) AS nombre_lignes
        FROM read_csv(
            '{chemin_csv}',
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

    print("\nNombre de lignes par département :")
    print(resultat.to_string(index=False))

    total = int(resultat["nombre_lignes"].sum())
    print(f"\nTotal des lignes PACA : {total:,}".replace(",", " "))


# ============================================================
# EXPLORATION DU PARQUET
# ============================================================

def explorer_parquet(con):
    print("\n" + "=" * 60)
    print("2. EXPLORATION DU PARQUET")
    print("=" * 60)

    if not FICHIER_PARQUET.exists():
        print("\nFichier Parquet introuvable.")
        print("Il faut d'abord générer le fichier Parquet.")
        return

    chemin_parquet = FICHIER_PARQUET.as_posix().replace("'", "''")

    requete = f"""
        SELECT
            LPAD(TRIM(coddep), 2, '0') AS departement,
            COUNT(*) AS nombre_lignes,
            MIN(datemut) AS date_min,
            MAX(datemut) AS date_max
        FROM read_parquet('{chemin_parquet}')
        GROUP BY LPAD(TRIM(coddep), 2, '0')
        ORDER BY departement
    """

    resultat = con.execute(requete).fetchdf()

    print("\nRépartition des données dans le Parquet :")
    print(resultat.to_string(index=False))

    total = int(resultat["nombre_lignes"].sum())
    print(f"\nTotal des lignes Parquet : {total:,}".replace(",", " "))


# ============================================================
# VÉRIFICATION DES CODES DÉPARTEMENTAUX
# ============================================================

def verifier_departements(con):
    print("\n" + "=" * 60)
    print("3. VÉRIFICATION DES DÉPARTEMENTS")
    print("=" * 60)

    chemin_csv = FICHIER_SOURCE.as_posix().replace("'", "''")

    requete = f"""
        SELECT DISTINCT
            LPAD(TRIM(coddep), 2, '0') AS departement
        FROM read_csv(
            '{chemin_csv}',
            delim='|',
            header=true,
            all_varchar=true,
            sample_size=-1
        )
        ORDER BY departement
    """

    resultat = con.execute(requete).fetchdf()

    departements_trouves = set(
        resultat["departement"].astype(str)
    )
    departements_attendus = set(DEPARTEMENTS_PACA)

    print("\nDépartements trouvés :")
    print(", ".join(sorted(departements_trouves)))

    manquants = departements_attendus - departements_trouves

    if manquants:
        print("\nDépartements PACA manquants :")
        print(", ".join(sorted(manquants)))
    else:
        print("\nLes six départements PACA sont présents dans le CSV.")


# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================

def main():
    con = duckdb.connect()

    try:
        explorer_csv(con)
        explorer_parquet(con)
        verifier_departements(con)

    finally:
        con.close()

    print("\n" + "=" * 60)
    print("EXPLORATION TERMINÉE")
    print("=" * 60)


if __name__ == "__main__":
    main()