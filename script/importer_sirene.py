from pathlib import Path
from io import StringIO

import pandas as pd
import psycopg

from db_config import DB_CONFIG


# --------------------------------------------------
# 1. Chemins des fichiers Parquet
# --------------------------------------------------

fichier_etablissements = Path(
    r"C:\Users\Utilisateur\Desktop\projet-data-promoteurs-paca\data\processed\sirene\sirene_etablissements_actifs_paca.parquet"
)

fichier_unites_legales = Path(
    r"C:\Users\Utilisateur\Desktop\projet-data-promoteurs-paca\data\processed\sirene\sirene_unites_legales_immobilier_actif.parquet"
)


# --------------------------------------------------
# 2. Paramètres de connexion PostgreSQL
# --------------------------------------------------



# --------------------------------------------------
# 3. Fichiers et tables à importer
# --------------------------------------------------

imports = [
    (fichier_etablissements, "etablissements_sirene"),
    (fichier_unites_legales, "unites_legales_sirene"),
]


# --------------------------------------------------
# 4. Vérifier que les fichiers existent
# --------------------------------------------------

for fichier, nom_table in imports:
    if not fichier.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {fichier}"
        )


# --------------------------------------------------
# 5. Importer les fichiers dans PostgreSQL
# --------------------------------------------------

with psycopg.connect(**DB_CONFIG) as conn:

    with conn.cursor() as cur:

        for fichier, nom_table in imports:

            print(f"\nLecture du fichier : {fichier.name}")

            # Lire le fichier Parquet
            df = pd.read_parquet(fichier)

            print(f"Nombre de lignes : {len(df):,}")
            print(f"Nombre de colonnes : {len(df.columns)}")
            print(f"Colonnes : {df.columns.tolist()}")

            # Convertir les colonnes en texte
            df = df.astype("string")

            colonnes = list(df.columns)

            # Construire les définitions SQL
            definitions = ", ".join(
                f'"{colonne}" TEXT'
                for colonne in colonnes
            )

            # Supprimer la table si elle existe déjà
            # ATTENTION : cela efface son contenu
            cur.execute(
                f'DROP TABLE IF EXISTS public."{nom_table}" CASCADE;'
            )

            # Créer la table
            cur.execute(
                f"""
                CREATE TABLE public."{nom_table}" (
                    {definitions}
                );
                """
            )

            print(f"Table public.{nom_table} créée.")

            # Préparer les données au format CSV en mémoire
            buffer = StringIO()

            df.to_csv(
                buffer,
                index=False,
                header=False,
                na_rep=r"\N",
            )

            buffer.seek(0)

            # Préparer les noms des colonnes
            colonnes_sql = ", ".join(
                f'"{colonne}"'
                for colonne in colonnes
            )

            # Importer les données avec COPY
            with cur.copy(
                f"""
                COPY public."{nom_table}" ({colonnes_sql})
                FROM STDIN
                WITH (FORMAT CSV, NULL '\\N')
                """
            ) as copy:

                while True:
                    bloc = buffer.read(1024 * 1024)

                    if not bloc:
                        break

                    copy.write(bloc)

            print(
                f"Import terminé : {len(df):,} lignes "
                f"dans public.{nom_table}."
            )

            # Libérer la mémoire
            del df
            del buffer

    # Valider les imports
    conn.commit()


# --------------------------------------------------
# 6. Message final
# --------------------------------------------------

print("\nLes deux imports SIRENE sont terminés avec succès.")