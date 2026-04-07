-- Projekt: B2C-Marketing fuer Photovoltaik in Zuerich
-- Zweck: Dach-Kennzahlen auf Quartiere aggregieren

DROP MATERIALIZED VIEW IF EXISTS mart.quartier_roof_metrics CASCADE;

CREATE MATERIALIZED VIEW mart.quartier_roof_metrics AS
SELECT
    q.quartier_id,
    q.quartier_name,
    COUNT(r.roof_id) AS top_roof_count,
    COALESCE(SUM(r.roof_area_m2), 0)::numeric(14,2) AS roof_area_sum_m2,
    COALESCE(SUM(r.annual_yield_kwh), 0)::numeric(14,2) AS annual_yield_sum_kwh,
    COALESCE(AVG(r.annual_yield_kwh), 0)::numeric(14,2) AS annual_yield_avg_kwh,
    ROUND(
        COUNT(r.roof_id)::numeric / NULLIF(ST_Area(q.geom) / 1000000.0, 0),
        2
    ) AS top_roofs_per_km2,
    q.median_income_chf,
    q.owner_occupancy_rate,
    q.single_family_share,
    q.population_total,
    q.households_total,
    q.geom
FROM core.quartiers_enriched q
LEFT JOIN core.roofs_top_candidates r
    ON ST_Intersects(r.geom, q.geom)
GROUP BY
    q.quartier_id,
    q.quartier_name,
    q.median_income_chf,
    q.owner_occupancy_rate,
    q.single_family_share,
    q.population_total,
    q.households_total,
    q.geom;

COMMENT ON MATERIALIZED VIEW mart.quartier_roof_metrics IS 'Quartierbezogene Dach- und Demografie-Kennzahlen fuer das Python-Scoring';

CREATE UNIQUE INDEX IF NOT EXISTS idx_quartier_roof_metrics_quartier_id
    ON mart.quartier_roof_metrics (quartier_id);

CREATE INDEX IF NOT EXISTS idx_quartier_roof_metrics_geom
    ON mart.quartier_roof_metrics
    USING GIST (geom);

ANALYZE mart.quartier_roof_metrics;

-- Optional: priorisierte Strassenzuege als Erweiterung
DROP MATERIALIZED VIEW IF EXISTS mart.street_segments_priority CASCADE;

DO $$
BEGIN
    IF to_regclass('raw.osm_streets_raw') IS NOT NULL THEN
        EXECUTE '
            CREATE MATERIALIZED VIEW mart.street_segments_priority AS
            SELECT
                s.gid,
                COALESCE(s.name, ''Unbenannte Strasse'') AS street_name,
                COUNT(r.roof_id) AS nearby_top_roofs,
                COALESCE(SUM(r.annual_yield_kwh), 0)::numeric(14,2) AS nearby_yield_kwh,
                s.geom
            FROM raw.osm_streets_raw s
            LEFT JOIN core.roofs_top_candidates r
                ON ST_DWithin(s.geom, ST_Centroid(r.geom), 25)
            GROUP BY s.gid, s.name, s.geom
        ';

        EXECUTE '
            CREATE INDEX IF NOT EXISTS idx_street_segments_priority_geom
                ON mart.street_segments_priority
                USING GIST (geom)
        ';

        EXECUTE 'ANALYZE mart.street_segments_priority';
    ELSE
        RAISE NOTICE 'raw.osm_streets_raw nicht vorhanden: optionale Strassenzug-Logik wird uebersprungen.';
    END IF;
END $$;
