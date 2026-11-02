from pathlib import Path

import geopandas as gpd


# Chemin du fichier GeoJSON
fichier_geojson = Path(
    r"C:\Users\Utilisateur\Desktop\projet-data-promoteurs-paca\data\exports\communes-100m.geojson"
)


# Vérifier l'existence du fichier
print("Fichier trouvé :", fichier_geojson.exists())

if fichier_geojson.exists():

    # Lire les contours des communes
    communes = gpd.read_file(fichier_geojson)

    # Afficher les informations principales
    print("\n--- Informations sur les communes ---")
    print(f"Nombre de communes : {len(communes):,}")
    print(f"Nombre de colonnes : {len(communes.columns)}")

    # Afficher les colonnes
    print("\nColonnes disponibles :")
    print(communes.columns.tolist())

    # Afficher le système de coordonnées
    print("\nSystème de coordonnées :")
    print(communes.crs)

    # Afficher les trois premières communes
    print("\nAperçu des 3 premières communes :")
    print(communes.head(3))

else:
    print(
        "\nFichier introuvable. "
        "Vérifie le chemin et le nom du fichier."
    )