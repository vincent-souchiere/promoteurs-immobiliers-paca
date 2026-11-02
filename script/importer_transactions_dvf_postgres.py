from pathlib import Path

import pandas as pd
import psycopg
import pyarrow.parquet as pq

from db_config import DB_CONFIG

# ==================================================
# 1. CHEMINS ET CONFIGURATION
# ==================================================

RACINE_PROJET = Path(__file__).resolve().parent.parent

FICHIER_PARQUET = (
    RACINE_PROJET
    / "data"
    / "processed"
    / "dvf"
    / "dvf_plus_paca_2026_02.parquet"
)

NOM_TABLE = "transactions_dvf"
NOM_TABLE_TEMP = "transactions_dvf_import_temp"

TAILLE_LOT = 20_000

DEPARTEMENTS_ATTENDUS = {"04", "05", "06", "13", "83", "84"}
NOMBRE_LIGNES_ATTENDU = 1_573_117


# ==================================================
# 2. VÉRIFICATION DU PARQUET
# ==================================================

def verifier_parquet():
    print("=" * 60)
    print("1. VÉRIFICATION DU PARQUET")
    print("=" * 60)

    if not FICHIER_PARQUET.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {FICHIER_PARQUET}"
        )

    parquet = pq.ParquetFile(FICHIER_PARQUET)
    colonnes = parquet.schema_arrow.names
    nombre_lignes = parquet.metadata.num_rows

    print(f"Fichier : {FICHIER_PARQUET}")
    print(f"Nombre de colonnes : {len(colonnes)}")
    print(f"Nombre de lignes : {nombre_lignes:,}".replace(",", " "))

    if nombre_lignes != NOMBRE_LIGNES_ATTENDU:
        raise ValueError(
            f"Nombre de lignes inattendu : {nombre_lignes:,}. "
            f"Attendu : {NOMBRE_LIGNES_ATTENDU:,}."
            .replace(",", " ")
        )

    if "coddep" not in colonnes:
        raise ValueError(
            "La colonne 'coddep' est absente du Parquet."
        )

    import duckdb

    con = duckdb.connect()
    chemin = FICHIER_PARQUET.as_posix().replace("'", "''")

    try:
        resultat = con.execute(
            f"""
            SELECT
                LPAD(TRIM(coddep), 2, '0') AS departement,
                COUNT(*) AS nombre_lignes
            FROM read_parquet('{chemin}')
            GROUP BY LPAD(TRIM(coddep), 2, '0')
            ORDER BY departement
            """
        ).fetchdf()
    finally:
        con.close()

    departements_trouves = set(
        resultat["departement"].astype(str)
    )

    print("\nRépartition des départements :")
    print(resultat.to_string(index=False))

    if departements_trouves != DEPARTEMENTS_ATTENDUS:
        raise ValueError(
            "Les départements du Parquet ne correspondent pas "
            "aux six départements PACA attendus."
        )

    print("\nVérification du Parquet réussie.")

    return colonnes, nombre_lignes


# ==================================================
# 3. IMPORT DANS UNE TABLE TEMPORAIRE
# ==================================================

def importer_dans_table_temporaire(
    connexion,
    colonnes,
):
    print("\n" + "=" * 60)
    print("2. IMPORT DANS LA TABLE TEMPORAIRE")
    print("=" * 60)

    definitions = ", ".join(
        f'"{colonne}" TEXT'
        for colonne in colonnes
    )

    colonnes_sql = ", ".join(
        f'"{colonne}"'
        for colonne in colonnes
    )

    placeholders = ", ".join(
        ["%s"] * len(colonnes)
    )

    requete_insert = (
        f"INSERT INTO public.{NOM_TABLE_TEMP} "
        f"({colonnes_sql}) "
        f"VALUES ({placeholders})"
    )

    # La table temporaire ne contient que les données du nouvel import.
    # La table principale n'est pas modifiée à cette étape.
    with connexion.cursor() as curseur:
        curseur.execute(
            f"""
            CREATE TABLE public.{NOM_TABLE_TEMP} (
                {definitions}
            );
            """
        )

    connexion.commit()

    parquet = pq.ParquetFile(FICHIER_PARQUET)
    total = 0

    for lot in parquet.iter_batches(batch_size=TAILLE_LOT):
        df = lot.to_pandas()

        lignes = [
            tuple(
                None if pd.isna(valeur) else str(valeur)
                for valeur in ligne
            )
            for ligne in df.itertuples(index=False, name=None)
        ]

        with connexion.cursor() as curseur:
            curseur.executemany(requete_insert, lignes)

        connexion.commit()

        total += len(lignes)

        print(
            f"Lignes importées : {total:,}".replace(",", " ")
        )

    print(
        f"\nImport temporaire terminé : {total:,} lignes."
        .replace(",", " ")
    )

    return total


# ==================================================
# 4. CONTRÔLE DE LA TABLE TEMPORAIRE
# ==================================================

def verifier_table_temporaire(connexion, nombre_attendu):
    print("\n" + "=" * 60)
    print("3. CONTRÔLE DE LA TABLE TEMPORAIRE")
    print("=" * 60)

    with connexion.cursor() as curseur:
        curseur.execute(
            f"""
            SELECT
                coddep,
                COUNT(*)
            FROM public.{NOM_TABLE_TEMP}
            GROUP BY coddep
            ORDER BY coddep;
            """
        )

        repartition = curseur.fetchall()

        curseur.execute(
            f"""
            SELECT COUNT(*)
            FROM public.{NOM_TABLE_TEMP};
            """
        )

        total = curseur.fetchone()[0]

    print("\nRépartition dans PostgreSQL :")

    for departement, nombre in repartition:
        print(f"{departement} : {nombre:,}".replace(",", " "))

    print(f"\nTotal : {total:,}".replace(",", " "))

    if total != nombre_attendu:
        raise ValueError(
            f"Le total importé ({total}) ne correspond pas "
            f"au total attendu ({nombre_attendu})."
        )

    departements_trouves = {
        str(departement).strip().zfill(2)
        for departement, _ in repartition
    }

    if departements_trouves != DEPARTEMENTS_ATTENDUS:
        raise ValueError(
            "La table temporaire ne contient pas les six "
            "départements attendus."
        )

    print("\nContrôle réussi.")


# ==================================================
# 5. REMPLACEMENT DE LA TABLE PRINCIPALE
# ==================================================

def remplacer_table_principale(connexion):
    print("\n" + "=" * 60)
    print("4. REMPLACEMENT DE LA TABLE PRINCIPALE")
    print("=" * 60)

    with connexion.cursor() as curseur:
        # Vérifie que la table cible existe.
        curseur.execute(
            """
            SELECT to_regclass('public.transactions_dvf');
            """
        )

        table_existante = curseur.fetchone()[0]

        if table_existante is None:
            # Première installation : la table temporaire devient
            # la table principale.
            curseur.execute(
                f"""
                ALTER TABLE public.{NOM_TABLE_TEMP}
                RENAME TO {NOM_TABLE};
                """
            )

        else:
            # On conserve la table existante et ses dépendances.
            # On retire ses anciennes lignes, puis on copie les
            # données de la table temporaire avec le nouveau schéma.
            #
            # Cette stratégie suppose que les dépendances existantes
            # tolèrent les colonnes ajoutées et que les types soient
            # compatibles.
            curseur.execute(
                f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = '{NOM_TABLE}';
                """
            )

            colonnes_existantes = {
                ligne[0] for ligne in curseur.fetchall()
            }

            parquet = pq.ParquetFile(FICHIER_PARQUET)
            colonnes_nouvelles = set(
                parquet.schema_arrow.names
            )

            if colonnes_existantes != colonnes_nouvelles:
                raise RuntimeError(
                    "La structure de la table existante diffère "
                    "du Parquet. Le remplacement automatique est "
                    "interrompu pour protéger les dépendances "
                    "éventuelles. La table temporaire a été conservée."
                )

            curseur.execute(
                f"TRUNCATE TABLE public.{NOM_TABLE};"
            )

            curseur.execute(
                f"""
                INSERT INTO public.{NOM_TABLE}
                SELECT *
                FROM public.{NOM_TABLE_TEMP};
                """
            )

            curseur.execute(
                f"DROP TABLE public.{NOM_TABLE_TEMP};"
            )

    connexion.commit()

    print("Remplacement terminé.")


# ==================================================
# 6. PROGRAMME PRINCIPAL
# ==================================================

def main():
    colonnes, nombre_attendu = verifier_parquet()

    print("\nConnexion à PostgreSQL...")

    with psycopg.connect(**DB_CONFIG) as connexion:
        try:
            # Évite de supprimer une table temporaire existante :
            # elle pourrait contenir un import précédent à examiner.
            with connexion.cursor() as curseur:
                curseur.execute(
                    """
                    SELECT to_regclass(
                        'public.transactions_dvf_import_temp'
                    );
                    """
                )

                temporaire_existante = curseur.fetchone()[0]

            if temporaire_existante is not None:
                raise RuntimeError(
                    "La table temporaire transactions_dvf_import_temp "
                    "existe déjà. Vérifie son contenu dans pgAdmin "
                    "avant de poursuivre."
                )

            total = importer_dans_table_temporaire(
                connexion,
                colonnes,
            )

            if total != nombre_attendu:
                raise ValueError(
                    "Le nombre de lignes importées ne correspond "
                    "pas au nombre de lignes du Parquet."
                )

            verifier_table_temporaire(
                connexion,
                nombre_attendu,
            )

            remplacer_table_principale(connexion)

        except Exception:
            connexion.rollback()
            raise

    print("\n" + "=" * 60)
    print("IMPORT TERMINÉ")
    print("=" * 60)
    print(f"Table : public.{NOM_TABLE}")
    print(
        f"Nombre de lignes : {nombre_attendu:,}".replace(",", " ")
    )


if __name__ == "__main__":
    main()