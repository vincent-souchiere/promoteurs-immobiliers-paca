from pathlib import Path
import pyarrow.parquet as pq
import pandas as pd

racine = Path(__file__).resolve().parent.parent
fichier = (
    racine
    / "data"
    / "processed"
    / "cadastre"
    / "parcelles_paca.parquet"
)

if not fichier.exists():
    raise FileNotFoundError(f"Fichier introuvable : {fichier}")

parquet = pq.ParquetFile(fichier)

print("Fichier :", fichier)
print("Nombre de lignes :", f"{parquet.metadata.num_rows:,}")
print("Nombre de groupes :", parquet.metadata.num_row_groups)

print("\nStructure des colonnes :")
print(parquet.schema)

print("\nExemple de 3 parcelles :")

colonnes = [
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

df = pd.read_parquet(
    fichier,
    columns=colonnes,
).head(3)

for _, ligne in df.iterrows():
    print("\n--- Parcelle ---")
    for colonne, valeur in ligne.items():
        if colonne == "geometry" and isinstance(valeur, bytes):
            print("geometry :", f"{len(valeur)} octets")
            print("Début des données :", valeur[:20].hex())
        else:
            print(f"{colonne} :", valeur)
