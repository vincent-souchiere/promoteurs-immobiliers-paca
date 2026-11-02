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

FICHIER_SORTIE = (
    RACINE_PROJET
    / "data"
    / "processed"
    / "dvf"
    / "dvf_plus_paca_2026_02.parquet"
)

DEPARTEMENTS_PACA = ("04", "05", "06", "13", "83", "84")

NOMBRE_LIGNES_ATTENDU = 1_573_117


# ============================================================
# CONVERSION DU CSV VERS PARQUET
# ============================================================

def convertir_csv_vers_parquet(con):
    print("=" * 70)
    print("1. CONVERSION DU CSV VERS PARQUET")
    print("=" * 70)

    if not FICHIER_SOURCE.exists():
        raise FileNotFoundError(
            f"Fichier source introuvable : {FICHIER_SOURCE}"
        )

    FICHIER_SORTIE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    chemin_csv = FICHIER_SOURCE.as_posix().replace("'", "''")
    chemin_parquet = FICHIER_SORTIE.as_posix().replace("'", "''")

    print(f"\nFichier source : {FICHIER_SOURCE}")
    print(f"Fichier de sortie : {FICHIER_SORTIE}")
    print("\nLecture du CSV et filtrage des six départements PACA...")

    requete = f"""
        COPY (
            SELECT
                * EXCLUDE (coddep),
                LPAD(TRIM(coddep), 2, '0') AS coddep
            FROM read_csv(
                '{chemin_csv}',
                delim='|',
                header=true,
                all_varchar=true,
                sample_size=-1
            )
            WHERE LPAD(TRIM(coddep), 2, '0')
                IN ('04', '05', '06', '13', '83', '84')
        )
        TO '{chemin_parquet}'
        (FORMAT PARQUET, COMPRESSION ZSTD);
    """

    con.execute(requete)

    print("\nConversion terminée.")


# ============================================================
# VÉRIFICATION DU PARQUET
# ============================================================

def verifier_parquet(con):
    print("\n" + "=" * 70)
    print("2. VÉRIFICATION DU FICHIER PARQUET")
    print("=" * 70)

    if not FICHIER_SORTIE.exists():
        raise FileNotFoundError(
            f"Fichier Parquet introuvable : {FICHIER_SORTIE}"
        )

    chemin_parquet = FICHIER_SORTIE.as_posix().replace("'", "''")

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

    print("\nRépartition des lignes par département :")
    print(resultat.to_string(index=False))

    total = int(resultat["nombre_lignes"].sum())

    departements_trouves = set(
        resultat["departement"].astype(str)
    )
    departements_attendus = set(DEPARTEMENTS_PACA)

    print(
        f"\nNombre total de lignes : {total:,}".replace(",", " ")
    )

    if departements_trouves != departements_attendus:
        departements_manquants = (
            departements_attendus - departements_trouves
        )
        departements_inattendus = (
            departements_trouves - departements_attendus
        )

        raise ValueError(
            "Les départements présents dans le Parquet ne correspondent "
            "pas aux six départements PACA. "
            f"Manquants : {sorted(departements_manquants)} ; "
            f"inattendus : {sorted(departements_inattendus)}"
        )

    if total != NOMBRE_LIGNES_ATTENDU:
        raise ValueError(
            f"Nombre de lignes inattendu : {total:,}. "
            f"Nombre attendu : {NOMBRE_LIGNES_ATTENDU:,}."
            .replace(",", " ")
        )

    print("\nVérification réussie : les six départements sont présents.")
    print("Le nombre total de lignes correspond au CSV source.")


# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================

def main():
    print("DÉMARRAGE DE LA CONVERSION DVF+ PACA")

    con = duckdb.connect()

    try:
        convertir_csv_vers_parquet(con)
        verifier_parquet(con)

    finally:
        con.close()

    print("\n" + "=" * 70)
    print("CONVERSION ET VÉRIFICATION TERMINÉES AVEC SUCCÈS")
    print("=" * 70)
    print(f"\nFichier Parquet généré : {FICHIER_SORTIE}")


if __name__ == "__main__":
    main()