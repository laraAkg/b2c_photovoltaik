-- Projekt: B2C-Marketing fuer Photovoltaik in Zuerich
-- Zweck: Datenbankstruktur und Basiskonfiguration

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS mart;

COMMENT ON SCHEMA raw IS 'Rohimporte ohne fachliche Bereinigung';
COMMENT ON SCHEMA core IS 'Bereinigte und fachlich vorbereitete Basisobjekte';
COMMENT ON SCHEMA mart IS 'Analyse- und Exportobjekte fuer Python und QGIS';

-- Erwartete Rohobjekte nach dem Import:
-- raw.bfe_roofs_raw
-- raw.zurich_quartiers_raw
-- raw.demography_quartier_raw
-- optional raw.osm_streets_raw

-- Sinnvolle Standardkonventionen:
-- - geom als Geometriespalte
-- - quartier_id als technischer Schluessel auf Quartierebene
-- - alle fachlichen Views materialisiert erst ab bereinigter Basis

-- Leere Zieltabellen fuer Python-Rueckschreibungen koennen bewusst erst spaeter erzeugt werden.

ANALYZE;

-- Wartungshinweis:
-- Nach groesseren Importen und Materialized Views:
-- VACUUM ANALYZE raw.bfe_roofs_raw;
-- VACUUM ANALYZE raw.zurich_quartiers_raw;
-- VACUUM ANALYZE raw.demography_quartier_raw;
