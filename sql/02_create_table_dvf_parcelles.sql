-- 1. Supprimer la table existante
DROP TABLE IF EXISTS public.dvf_parcelles;


-- 2. Recréer la table dvf_parcelles
CREATE TABLE public.dvf_parcelles AS
SELECT
    d.idmutation AS idmutation_dvf,
    d.datemut AS date_mutation,
    d.valeurfonc AS prix,
    LPAD(TRIM(d.coddep), 2, '0') AS code_departement,
    d.l_codinsee AS code_commune,
    d.libnatmut AS type_mutation,
    d.sbati AS surface_batie,

    -- Coordonnées géographiques DVF+
    d.geompar_x AS longitude,
    d.geompar_y AS latitude,

    -- Parcelle cadastrale
    TRIM(ref.id_parcelle) AS id_parcelle,

    -- Informations cadastrales
    p.contenance AS contenance_cadastrale,
    p.section AS section,
    p.millesime AS millesime

FROM public.transactions_dvf AS d

CROSS JOIN LATERAL
    UNNEST(
        STRING_TO_ARRAY(d.l_idpar, ',')
    ) AS ref(id_parcelle)

LEFT JOIN public.parcelles AS p
    ON TRIM(ref.id_parcelle) = p.id_parcelle

WHERE NULLIF(TRIM(d.l_idpar), '') IS NOT NULL;


-- 3. Vérifier la répartition par département
SELECT
    code_departement,
    COUNT(*) AS nombre_lignes,
    ROUND(
        100.0 * COUNT(*) / NULLIF(SUM(COUNT(*)) OVER (), 0),
        2
    ) AS part_pct
FROM public.dvf_parcelles
GROUP BY code_departement
ORDER BY code_departement;


-- 4. Vérifier les coordonnées
SELECT
    COUNT(*) AS nombre_total,
    COUNT(*) FILTER (
        WHERE longitude IS NOT NULL
          AND latitude IS NOT NULL
    ) AS nombre_avec_coordonnees,
    COUNT(*) FILTER (
        WHERE longitude IS NULL
           OR latitude IS NULL
    ) AS nombre_sans_coordonnees
FROM public.dvf_parcelles;