-- Projet : Analyse des promoteurs immobiliers en PACA
-- Objectif : Découper les références cadastrales de DVF
--            et les rapprocher des parcelles cadastrales.
-- Attention : cette requête sert à tester la jointure.

SELECT
d.idmutation,
d.datemut,
d.valeurfonc,
d.coddep,
d.l_codinsee,
TRIM(ref.id_parcelle) AS id_parcelle,
p.contenance,
p.section,
p.millesime
FROM public.transactions_dvf AS d

CROSS JOIN LATERAL    /* On découpe l_idpar pour obtenir une référence cadastrale par ligne. */
UNNEST(STRING_TO_ARRAY(d.l_idpar, ',')) AS ref(id_parcelle) -- UNNEST transforme les éléments d'un tableau en lignes distinctes.

LEFT JOIN public.parcelles AS p
ON TRIM(ref.id_parcelle) = p.id_parcelle  /* On indique à PostgreSQL comment reconnaître une correspondance entre les deux tables. */

WHERE NULLIF(TRIM(d.l_idpar), '') IS NOT NULL

ORDER BY d.idmutation
LIMIT 20;
