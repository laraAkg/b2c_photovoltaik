-- Projekt: B2C-Marketing fuer Photovoltaik in Zuerich
-- Zweck: Klare Exportobjekte fuer Python und QGIS
-- mart.quartier_targeting_results wird nach dem Python-Scoring erzeugt oder ersetzt.

DROP VIEW IF EXISTS mart.v_quartier_scoring_input CASCADE;
DROP VIEW IF EXISTS mart.top_roofs_for_campaign CASCADE;

CREATE OR REPLACE VIEW mart.v_quartier_scoring_input AS
SELECT
    quartier_id,
    quartier_name,
    top_roof_count,
    roof_area_sum_m2,
    annual_yield_sum_kwh,
    annual_yield_avg_kwh,
    top_roofs_per_km2,
    median_income_chf,
    owner_occupancy_rate,
    single_family_share,
    population_total,
    households_total,
    geom
FROM mart.quartier_roof_metrics;

COMMENT ON VIEW mart.v_quartier_scoring_input IS 'Python-Eingangsdaten fuer das Marketing-Scoring';

CREATE OR REPLACE VIEW mart.top_roofs_for_campaign AS
SELECT
    r.roof_id,
    r.suitability_class,
    r.roof_area_m2,
    r.annual_yield_kwh,
    r.solar_radiation_kwh_m2,
    q.quartier_id,
    q.quartier_name,
    r.geom
FROM core.roofs_top_candidates r
LEFT JOIN core.quartiers_prepared q
    ON ST_Intersects(r.geom, q.geom);

COMMENT ON VIEW mart.top_roofs_for_campaign IS 'Top-Daecher fuer QGIS und vertriebliche Detailkarten';

-- QGIS-Exportbeispiele:
-- ogr2ogr -f GPKG exports/quartier_targeting_results.gpkg PG:"host=localhost dbname=pv_marketing_zh user=postgres password=postgres" mart.quartier_targeting_results
-- ogr2ogr -f GPKG exports/top_roofs_for_campaign.gpkg PG:"host=localhost dbname=pv_marketing_zh user=postgres password=postgres" mart.top_roofs_for_campaign
