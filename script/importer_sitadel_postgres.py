from pathlib import Path

import pandas as pd
import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

from db_config import DB_CONFIG

# Chemins du projet
RACINE = Path(__file__).resolve().parent.parent
FICHIER = (
    RACINE
    / "data"
    / "processed"
    / "sitadel"
    / "sitadel_autorisations_logements_paca.parquet"
)


TABLE = "permis_construire_sitadel"


def nom_colonne(nom):
    """Normalise les noms de colonnes pour PostgreSQL."""
    import re
    nom = str(nom).strip().lower()
    nom = re.sub(r"[^a-z0-9_]+", "_", nom)
    nom = re.sub(r"_+", "_", nom).strip("_")
    if not nom or nom[0].isdigit():
        nom = "col_" + nom
    return nom


def main():
    if not FICHIER.exists():
        raise FileNotFoundError(f"Fichier introuvable : {FICHIER}")

    print(f"Lecture du fichier : {FICHIER}")
    df = pd.read_parquet(FICHIER)

    # Évite les collisions si plusieurs noms deviennent identiques
    colonnes = []
    deja_vues = set()
    for colonne in df.columns:
        base = nom_colonne(colonne)
        nom = base
        compteur = 2
        while nom in deja_vues:
            nom = f"{base}_{compteur}"
            compteur += 1
        deja_vues.add(nom)
        colonnes.append(nom)

    df.columns = colonnes
    print(f"{len(df):,} lignes et {len(df.columns)} colonnes lues.")

    # Import générique : les colonnes sont d'abord stockées en texte.
    # Les valeurs manquantes deviennent NULL.
    df = df.astype(object).where(pd.notna(df), None)
    lignes = [
        tuple(
            valeur.isoformat() if hasattr(valeur, "isoformat") else valeur
            for valeur in ligne
        )
        for ligne in df.itertuples(index=False, name=None)
    ]

    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            # Arrête le script plutôt que d'écraser une table existante.
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
                    f"La table {TABLE} existe déjà. "
                    "Aucune donnée n'a été importée. "
                    "Vérifie son contenu avant de choisir la suite."
                )

            definitions = sql.SQL(", ").join(
                sql.SQL("{} TEXT").format(sql.Identifier(colonne))
                for colonne in df.columns
            )
            cur.execute(
                sql.SQL("CREATE TABLE {} ({})").format(
                    sql.Identifier(TABLE), definitions
                )
            )

            if lignes:
                requete = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                    sql.Identifier(TABLE),
                    sql.SQL(", ").join(
                        sql.Identifier(colonne) for colonne in df.columns
                    ),
                    sql.SQL(", ").join(
                        sql.Placeholder() for _ in df.columns
                    ),
                )
                cur.executemany(requete, lignes)

    print(f"Import terminé : {len(df):,} lignes dans {TABLE}.")


if __name__ == "__main__":
    main()