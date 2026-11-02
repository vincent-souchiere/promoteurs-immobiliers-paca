from pathlib import Path

import pyarrow.parquet as pq

racine = Path(__file__).resolve().parent.parent
fichier = racine / "data" / "processed" / "cadastre" / "parcelles_paca.parquet"

parquet = pq.ParquetFile(fichier)

print(f"Nombre total de parcelles : {parquet.metadata.num_rows:,}")

srid_trouves = set()
types_wkb = {}
geometries_vides = 0
geometries_absentes = 0
total = 0

for lot in parquet.iter_batches(
    batch_size=50_000,
    columns=["geom_srid", "geometry"],
):
    df = lot.to_pandas()

    for srid, geom in zip(df["geom_srid"], df["geometry"]):
        total += 1

        if srid is not None:
            srid_trouves.add(int(srid))

        if geom is None:
            geometries_absentes += 1
            continue

        geom = bytes(geom)

        if len(geom) == 0:
            geometries_vides += 1
            continue

        # Dans le WKB standard, le type géométrique suit l'ordre des octets.
        type_code = int.from_bytes(geom[1:5], byteorder="little")
        types_wkb[type_code] = types_wkb.get(type_code, 0) + 1

    if total % 500_000 == 0:
        print(f"Vérification : {total:,} parcelles")

print("\n--- Résultats ---")
print("Nombre vérifié :", f"{total:,}")
print("SRID rencontrés :", sorted(srid_trouves))
print("Types WKB rencontrés :", types_wkb)
print("Géométries absentes :", geometries_absentes)
print("Géométries vides :", geometries_vides)