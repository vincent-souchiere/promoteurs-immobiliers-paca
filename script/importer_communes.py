from pathlib import Path
from urllib.parse import quote_plus

import geopandas as gpd
from sqlalchemy import create_engine, text

from db_config import DB_CONFIG


# ============================================================
# 1. CHEMINS DU PROJET
# ============================================================

RACINE_PROJET = Path(__file__).resolve().parent.parent

FICHIER_GEOJSON = (
    RACINE_PROJET
    / "data"
    / "exports"
    / "communes-100m.geojson"
)


# ============================================================
# 2. PARAMÈTRES DE CONNEXION POSTGRESQL
# ============================================================

# ============================================================
# 3. CONSTRUIRE L'URL DE CONNEXION
# ============================================================

UTILISATEUR = quote_plus(DB_CONFIG["user"])
MOT_DE_PASSE = quote_plus(DB_CONFIG["password"])
HOTE = DB_CONFIG["host"]
PORT = DB_CONFIG["port"]
BASE = DB_CONFIG["dbname"]

URL_DB = (
    f"postgresql+psycopg2://{UTILISATEUR}:{MOT_DE_PASSE}"
    f"@{HOTE}:{PORT}/{BASE}"
)


# ============================================================
# 4. VÉRIFIER LE FICHIER GEOJSON
# ============================================================

if not FICHIER_GEOJSON.exists():
    raise FileNotFoundError(
        f"Fichier GeoJSON introuvable : {FICHIER_GEOJSON}"
    )

print(f"Fichier trouvé : {FICHIER_GEOJSON}")


# ============================================================
# 5. LIRE LES COMMUNES
# ============================================================

print("\nLecture du fichier GeoJSON...")

communes = gpd.read_file(FICHIER_GEOJSON)

print(f"Nombre de communes en France : {len(communes):,}")
print(f"Système de coordonnées : {communes.crs}")


# ============================================================
# 6. FILTRER LA RÉGION PROVENCE-ALPES-CÔTE D'AZUR
# ============================================================

# Code INSEE de la région PACA : 93
communes_paca = communes.loc[
    communes["region"].astype(str).eq("93")
].copy()

print(f"Nombre de communes PACA : {len(communes_paca):,}")

if communes_paca.empty:
    raise ValueError(
        "Aucune commune PACA trouvée. Vérifie la colonne 'region'."
    )


# ============================================================
# 7. PRÉPARER LES COLONNES
# ============================================================

communes_paca = communes_paca[
    [
        "code",
        "nom",
        "departement",
        "region",
        "geometry",
    ]
].copy()

communes_paca = communes_paca.rename(
    columns={
        "code": "code_commune",
        "nom": "nom_commune",
        "departement": "code_departement",
        "region": "code_region",
    }
)

communes_paca = communes_paca.set_crs(
    "EPSG:4326",
    allow_override=True,
)


# ============================================================
# 8. IMPORTER DANS POSTGRESQL
# ============================================================

print("\nConnexion à PostgreSQL...")

engine = create_engine(URL_DB)

try:
    with engine.connect() as connexion:
        connexion.execute(text("SELECT 1"))
        print("Connexion PostgreSQL réussie.")

        # Vérifier si la table cible existe déjà.
        table_existante = connexion.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name = 'communes_paca'
                );
                """
            )
        ).scalar()

    if table_existante:
        raise RuntimeError(
            "La table public.communes_paca existe déjà. "
            "Le script s'arrête pour éviter de l'écraser. "
            "Vérifie cette table avant de relancer l'importation."
        )

    print("\nImportation des communes PACA...")

    communes_paca.to_postgis(
        name="communes_paca",
        con=engine,
        schema="public",
        if_exists="fail",
        index=False,
    )

    print("Importation terminée.")

    # ========================================================
    # 9. VÉRIFIER L'IMPORTATION
    # ========================================================

    with engine.connect() as connexion:
        resultat = connexion.execute(
            text(
                """
                SELECT
                    COUNT(*) AS nombre_communes,
                    COUNT(*) FILTER (
                        WHERE geometry IS NOT NULL
                    ) AS communes_avec_geometrie
                FROM public.communes_paca;
                """
            )
        ).fetchone()

    print("\n--- Résultat de l'importation ---")
    print(f"Nombre de communes importées : {resultat[0]:,}")
    print(f"Communes avec géométrie : {resultat[1]:,}")

finally:
    engine.dispose()