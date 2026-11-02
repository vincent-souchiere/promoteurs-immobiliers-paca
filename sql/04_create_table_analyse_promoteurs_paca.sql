DROP TABLE IF EXISTS public.analyse_promoteurs_paca;

CREATE TABLE public.analyse_promoteurs_paca AS
SELECT
    -- 1 à 6 : Demandeur, établissement et localisation
    pc.siren_demandeur AS siren_demandeur_pc,
    pc.siret_demandeur AS siret_demandeur_pc,
    pc.nom_demandeur AS nom_demandeur_pc,
    e."dateCreationEtablissement" AS date_creation_etablissement,
    dp.id_parcelle,
    dp.longitude,
    dp.latitude,

    -- 7 à 13 : Transaction DVF et surfaces
    dp.idmutation_dvf,
    dp.date_mutation,
    dp.surface_batie,
    pc.superficie_terrain,
    pc.surface_habitable_creee,
    dp.prix,

    -- 14 à 20 : Localisation et cadastre
    dp.code_departement,
    dp.code_commune,
    e."libelleCommuneEtablissement" AS ville,
    dp.type_mutation,
    dp.contenance_cadastrale,
    dp.section,
    dp.millesime,

    -- 21 à 24 : Permis de construire
    pc.numero_dossier AS numero_dossier_pc,
    pc.date_autorisation AS date_autorisation_pc,
    pc.date_debut_travaux AS date_debut_travaux_pc,
    pc.date_achevement AS date_achevement_pc

FROM public.dvf_parcelles AS dp

LEFT JOIN public.permis_construire_sitadel AS pc
    ON TRIM(pc.code_departement) = TRIM(dp.code_departement)
   AND TRIM(pc.code_commune) = TRIM(dp.code_commune)
   AND (
        (
            TRIM(pc.section_cadastrale_1) = TRIM(dp.section)
            AND TRIM(pc.parcelle_cadastrale_1)
                = SUBSTRING(dp.id_parcelle FROM 11 FOR 4)
        )
        OR
        (
            TRIM(pc.section_cadastrale_2) = TRIM(dp.section)
            AND TRIM(pc.parcelle_cadastrale_2)
                = SUBSTRING(dp.id_parcelle FROM 11 FOR 4)
        )
        OR
        (
            TRIM(pc.section_cadastrale_3) = TRIM(dp.section)
            AND TRIM(pc.parcelle_cadastrale_3)
                = SUBSTRING(dp.id_parcelle FROM 11 FOR 4)
        )
   )

LEFT JOIN public.etablissements_sirene AS e
    ON NULLIF(TRIM(pc.siret_demandeur), '') IS NOT NULL
   AND TRIM(pc.siret_demandeur) = TRIM(e.siret);

COMMIT;