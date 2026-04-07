-- Projekt: B2C-Marketing fuer Photovoltaik in Zuerich
-- Zweck: Quartiere und Demografie auf gemeinsame Join-Logik bringen
-- WICHTIG: Quartier-Schluessel und Demografie-Feldnamen an lokale Daten anpassen.

DROP MATERIALIZED VIEW IF EXISTS core.quartiers_enriched CASCADE;
DROP VIEW IF EXISTS core.quartiers_prepared CASCADE;

CREATE OR REPLACE VIEW core.quartiers_prepared AS
SELECT
    q.gid,
    COALESCE(q.quartier_id::text, q.objectid::text, q.id::text) AS quartier_id,
    COALESCE(q.quartier_name, q.name, q.qname, 'Unbekanntes Quartier') AS quartier_name,
    CASE
        WHEN ST_SRID(q.geom) = 2056 THEN q.geom
        WHEN ST_SRID(q.geom) = 0 THEN ST_SetSRID(q.geom, 2056)
        ELSE ST_Transform(q.geom, 2056)
    END::geometry(MultiPolygon, 2056) AS geom
FROM raw.zurich_quartiers_raw q
WHERE q.geom IS NOT NULL;

COMMENT ON VIEW core.quartiers_prepared IS 'Quartiergrenzen in LV95 mit vereinheitlichter Quartier-ID';

CREATE MATERIALIZED VIEW core.quartiers_enriched AS
SELECT
    q.gid,
    q.quartier_id,
    q.quartier_name,
    d.median_income_chf,
    d.owner_occupancy_rate,
    d.single_family_share,
    d.population_total,
    d.households_total,
    q.geom
FROM core.quartiers_prepared q
LEFT JOIN raw.demography_quartier_raw d
    ON q.quartier_id = d.quartier_id::text;

COMMENT ON MATERIALIZED VIEW core.quartiers_enriched IS 'Quartiere mit angehaengten demografischen Kennzahlen';

CREATE UNIQUE INDEX IF NOT EXISTS idx_quartiers_enriched_quartier_id
    ON core.quartiers_enriched (quartier_id);

CREATE INDEX IF NOT EXISTS idx_quartiers_enriched_geom
    ON core.quartiers_enriched
    USING GIST (geom);

ANALYZE core.quartiers_enriched;

-- Datenqualitaetscheck
-- SELECT COUNT(*) FILTER (WHERE median_income_chf IS NULL) AS missing_income
-- FROM core.quartiers_enriched;
