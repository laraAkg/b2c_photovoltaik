-- Projekt: B2C-Marketing fuer Photovoltaik in Zuerich
-- Zweck: Dachdaten technisch pruefen, vereinheitlichen und filtern
-- WICHTIG: Platzhalter-Feldnamen vor dem ersten Run an das echte BFE-Schema anpassen.

DROP MATERIALIZED VIEW IF EXISTS core.roofs_top_candidates CASCADE;
DROP VIEW IF EXISTS core.roofs_prepared CASCADE;

-- 1. Rohdaten fuer die Zielanalyse standardisieren
CREATE OR REPLACE VIEW core.roofs_prepared AS
SELECT
    r.gid,
    -- Annahme: bereits vorhandene eindeutige Dach-ID, sonst Fallback auf gid
    COALESCE(r.roof_id::text, r.gid::text) AS roof_id,
    -- Annahme: Feld fuer Eignungsklasse, z. B. "eignung" oder "suitability"
    LOWER(TRIM(COALESCE(r.suitability_class, r.eignungsklasse, r.eignung, 'unbekannt'))) AS suitability_class,
    -- Annahme: Dachflaeche in Quadratmetern
    COALESCE(r.roof_area_m2, r.dachflaeche, r.area_m2)::numeric AS roof_area_m2,
    -- Annahme: erwarteter Jahresertrag in kWh
    COALESCE(r.annual_yield_kwh, r.stromertrag, r.electricity_yield_kwh)::numeric AS annual_yield_kwh,
    -- Annahme: Globalstrahlung oder Einstrahlung
    COALESCE(r.solar_radiation_kwh_m2, r.strahlung, r.global_radiation)::numeric AS solar_radiation_kwh_m2,
    CASE
        WHEN ST_SRID(r.geom) = 2056 THEN r.geom
        WHEN ST_SRID(r.geom) = 0 THEN ST_SetSRID(r.geom, 2056)
        ELSE ST_Transform(r.geom, 2056)
    END::geometry(MultiPolygon, 2056) AS geom
FROM raw.bfe_roofs_raw r
WHERE r.geom IS NOT NULL;

COMMENT ON VIEW core.roofs_prepared IS 'Rohe BFE-Daechern mit standardisierten Attributen und LV95-Geometrie';

-- 2. Fachliche Filter fuer vertriebsrelevante Daecher
CREATE MATERIALIZED VIEW core.roofs_top_candidates AS
SELECT
    gid,
    roof_id,
    suitability_class,
    roof_area_m2,
    annual_yield_kwh,
    solar_radiation_kwh_m2,
    geom
FROM core.roofs_prepared
WHERE suitability_class IN ('sehr gut', 'hervorragend', 'very good', 'excellent')
  AND roof_area_m2 >= 35
  AND annual_yield_kwh >= 4500;

COMMENT ON MATERIALIZED VIEW core.roofs_top_candidates IS 'Vertriebsrelevante PV-Daecher mit hoher Eignung, Mindestflaeche und Mindestjahresertrag';

CREATE INDEX IF NOT EXISTS idx_roofs_prepared_geom
    ON raw.bfe_roofs_raw
    USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_roofs_top_candidates_geom
    ON core.roofs_top_candidates
    USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_roofs_top_candidates_suitability
    ON core.roofs_top_candidates (suitability_class);

ANALYZE core.roofs_top_candidates;

-- CRS-Pruefung
-- SELECT DISTINCT ST_SRID(geom) FROM raw.bfe_roofs_raw;

-- Schnellcheck
-- SELECT suitability_class, COUNT(*) FROM core.roofs_top_candidates GROUP BY 1 ORDER BY 2 DESC;
