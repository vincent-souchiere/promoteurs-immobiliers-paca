from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import psycopg
from psycopg import sql

from db_config import DB_CONFIG


# ==================================================
# 1. CHEMINS ET CONFIGURATION
# ==================================================

RACINE = Path(__file__).resolve().parent.parent

FICHIER = (
    RACINE
    / "data"
    / "processed"
    / "cadastre"
    / "parcelles_paca.parquet"
)

TABLE = "parcelles"
TAILLE_LOT = 5_000

COLONNES = [
    "id_parcelle",
    "departement",
    "commune",
    "prefixe",
    "section",
    "parcelle",
    "contenance",
    "millesime",
    "geom_srid",
    "geometry",
]


# ==================================================
# 2. CONVERSION DES VALEURS SQL
# ==================================================

def valeur_sql(valeur):
    """Convertit les valeurs manquantes en NULL SQL."""

    if pd.isna(valeur):
        return None

    if hasattr(valeur, "item"):
        valeur = valeur.item()

    return valeur


# ==================================================
# 3. IMPORT DES PARCELLES
# ==================================================

def main():

    if not FICHIER.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {FICHIER}"
        )

    print("Lecture des métadonnées du fichier...")

    parquet = pq.ParquetFile(FICHIER)

    nombre_total = parquet.metadata.num_rows

    print(
        f"Nombre de parcelles à importer : {nombre_total:,}"
    )

    with psycopg.connect(**DB_CONFIG) as conn:

        with conn.cursor() as cur:

            # Vérifier que la table n'existe pas déjà.
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name = %s
                )
                """,
                (TABLE,),
            )

            if cur.fetchone()[0]:
                raise RuntimeError(
                    "La table public.parcelles existe déjà. "
                    "Arrêt pour éviter tout écrasement."
                )

            # Créer la table PostgreSQL.
            cur.execute(
                """
                CREATE TABLE public.parcelles (
                    id_parcelle TEXT PRIMARY KEY,
                    departement TEXT,
                    commune TEXT,
                    prefixe TEXT,
                    section TEXT,
                    parcelle TEXT,
                    contenance BIGINT,
                    millesime DATE,
                    geom_srid INTEGER,
                    geometry geometry(Geometry, 2154)
                )
                """
            )

            # Préparer la requête d'insertion.
            insertion = sql.SQL(
                """
                INSERT INTO public.parcelles (
                    id_parcelle,
                    departement,
                    commune,
                    prefixe,
                    section,
                    parcelle,
                    contenance,
                    millesime,
                    geom_srid,
                    geometry
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    ST_SetSRID(ST_GeomFromWKB(%s), %s)
                )
                """
            )

            total = 0

            # Importer les données par lots.
            for lot in parquet.iter_batches(
                batch_size=TAILLE_LOT,
                columns=COLONNES,
            ):

                df = lot.to_pandas()

                lignes = []

                for ligne in df.itertuples(
                    index=False,
                    name=None,
                ):

                    (
                        id_parcelle,
                        departement,
                        commune,
                        prefixe,
                        section,
                        parcelle,
                        contenance,
                        millesime,
                        geom_srid,
                        geometry,
                    ) = ligne

                    if geometry is None or geom_srid is None:
                        raise ValueError(
                            f"Géométrie ou SRID absent pour "
                            f"{id_parcelle}"
                        )

                    srid = int(geom_srid)

                    if srid != 2154:
                        raise ValueError(
                            f"SRID inattendu ({srid}) "
                            f"pour {id_parcelle}"
                        )

                    lignes.append(
                        (
                            valeur_sql(id_parcelle),
                            valeur_sql(departement),
                            valeur_sql(commune),
                            valeur_sql(prefixe),
                            valeur_sql(section),
                            valeur_sql(parcelle),
                            valeur_sql(contenance),
                            valeur_sql(millesime),
                            srid,
                            bytes(geometry),
                            srid,
                        )
                    )

                cur.executemany(insertion, lignes)

                total += len(lignes)

                print(
                    f"Importé : {total:,} / {nombre_total:,}"
                )

    print("\nImport terminé.")
    print(f"Table créée : public.{TABLE}")
    print(f"Lignes importées : {total:,}")


# ==================================================
# 4. EXÉCUTION DU PROGRAMME
# ==================================================

if __name__ == "__main__":
    main()