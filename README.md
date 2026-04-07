# B2C-Marketing fuer Photovoltaik: Die Jagd nach den besten Daechern

Praxisnaher Hochschulprototyp fuer das Modul "Einsatz von Geodaten im Marketing". Das Projekt verbindet technische Dach-Eignung aus dem Sonnendach-Datensatz mit demografischer Attraktivitaet auf Quartierebene in Zuerich. Ziel ist eine vertriebsnahe Priorisierung von Marketinggebieten fuer den Direktvertrieb von Photovoltaikanlagen.

## Projektidee

`sonnendach.ch` zeigt, welche Daechern technisch fuer Solarenergie geeignet sind. Fuer den Vertrieb reicht diese Information aber nicht aus: Ein technisch gutes Dach ist nicht automatisch ein wirtschaftlich attraktiver Lead. Dieses Projekt erweitert das reine Dachpotenzial um demografische Zielgruppenlogik und erzeugt daraus einen nachvollziehbaren Geomarketing-Score.

## Ziel

Identifikation von Quartieren in Zuerich, die sich besonders gut fuer eine gezielte Vermarktung von Photovoltaikanlagen eignen. Die Analyse soll Fachlichkeit, Datenbank-Workflow, Python-Scoring und QGIS-Visualisierung klar voneinander trennen.

## Forschungsfrage

Welche Quartiere in Zuerich eignen sich am besten fuer die gezielte Vermarktung von Photovoltaikanlagen, wenn man Solarpotenzial und demografische Merkmale gemeinsam betrachtet?

## Methodischer Rahmen

Das Projekt orientiert sich an einem klassischen Geomarketing-Workflow:

1. Oeffentliche Geodaten als Rohsignal laden
2. Technische Eignung in PostGIS vorqualifizieren
3. Dachpotenzial raeumlich auf Quartiere aggregieren
4. Quartiere mit demografischen Merkmalen anreichern
5. In Python einen transparenten Targeting-Score berechnen
6. Ergebnisse als vertriebstaugliche Entscheidungshilfe in QGIS visualisieren

## Pilotgebiet

Stadt Zuerich, Ziel-CRS `EPSG:2056` / LV95

## Datenquellen

### Pflichtdaten

- Bundesamt fuer Energie (BFE), Datensatz "Eignung von Hausdaechern fuer die Nutzung von Sonnenenergie" als GeoPackage
  - erwartete inhaltliche Felder: Eignungsklasse, Dachflaeche, Stromertrag, Strahlung, Geometrie
  - Fokus: sehr gute und hervorragende Daechern
- Statistische Quartiere der Stadt Zuerich
- Demografische Daten pro Quartier, mindestens:
  - Einkommen
  - optional: Eigentumsquote, Anteil Einfamilienhaeuser, Wohnungsstruktur

### Optionale Daten

- OpenStreetMap Strassen fuer eine Strassenzug-Logik
- swisstopo Basemap oder Gebaeudereferenz fuer die finale Kartenkomposition in QGIS

## Technologien

- PostgreSQL 14+
- PostGIS 3+
- Python 3.10+
- pandas
- GeoPandas
- SQLAlchemy
- psycopg2-binary
- shapely
- Jupyter oder Python-Skript
- QGIS 3.x

## Projektstruktur

```text
pv_b2c_photovoltaik_zuerich/
├── .env.example
├── README.md
├── requirements.txt
├── data_raw/
│   └── Ablage fuer originale Quelldaten (nicht versioniert)
├── data_processed/
│   └── Exportierte Zwischenstaende, CSV, GeoPackage
├── docs/
│   ├── methodology.md
│   └── pitch_notes.md
├── exports/
│   └── Finale Tabellenexporte fuer Abgabe oder Praesentation
├── notebooks/
│   └── Optionaler Platz fuer ein Notebook-Ableger des Python-Skripts
├── qgis/
│   └── README.md
├── sql/
│   ├── 01_create_schema.sql
│   ├── 02_prepare_roofs.sql
│   ├── 03_prepare_quartiers.sql
│   ├── 04_aggregate_to_quartiers.sql
│   └── 05_export_views.sql
└── src/
    └── targeting_analysis.py
```

### Zweck der wichtigsten Dateien

- `sql/01_create_schema.sql`: Datenbankstruktur, Schemas, Extensions, Zieltabellen und Importhinweise
- `sql/02_prepare_roofs.sql`: Dachdaten pruefen, auf LV95 transformieren, fachlich filtern und bereinigen
- `sql/03_prepare_quartiers.sql`: Quartiere und Demografie vereinheitlichen und fuer den Join vorbereiten
- `sql/04_aggregate_to_quartiers.sql`: Dach-KPIs je Quartier berechnen
- `sql/05_export_views.sql`: Endgueltige Export-Views fuer Python und QGIS
- `src/targeting_analysis.py`: Python-Analyse, Explorationsschritte, Scoring, Rueckschreiben nach PostGIS
- `docs/methodology.md`: Methodik, Annahmen, Gewichtungen, Datenlogik
- `docs/pitch_notes.md`: Praesentationsnotizen fuer einen 10-Minuten-Pitch
- `qgis/README.md`: Layer- und Visualisierungsempfehlungen fuer die Kartenerstellung
- `.env.example`: Verbindungsparameter und fachliche Schwellenwerte

## Installationsanleitung

### 1. Python-Umgebung

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. PostgreSQL / PostGIS

Eine lokale Datenbank anlegen, zum Beispiel:

```bash
createdb pv_marketing_zh
psql -d pv_marketing_zh -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

### 3. Umgebungsvariablen

`.env.example` nach `.env` kopieren und anpassen:

```bash
cp .env.example .env
```

## Import-Workflow

### GeoPackage nach PostGIS importieren

Beispiel fuer die Sonnendach-Daten:

```bash
ogr2ogr \
  -f PostgreSQL PG:"host=localhost dbname=pv_marketing_zh user=postgres password=postgres" \
  data_raw/sonnendach_zh.gpkg \
  -nln raw.bfe_roofs_raw \
  -lco GEOMETRY_NAME=geom \
  -lco FID=gid \
  -nlt PROMOTE_TO_MULTI
```

Beispiel fuer Quartiere:

```bash
ogr2ogr \
  -f PostgreSQL PG:"host=localhost dbname=pv_marketing_zh user=postgres password=postgres" \
  data_raw/statistische_quartiere_zh.gpkg \
  -nln raw.zurich_quartiers_raw \
  -lco GEOMETRY_NAME=geom \
  -lco FID=gid \
  -nlt PROMOTE_TO_MULTI
```

### CSV nach PostgreSQL importieren

```bash
psql -d pv_marketing_zh -c "\copy raw.demography_quartier_raw FROM 'data_raw/zurich_demography.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',')"
```

### Optional: OSM-Strassen importieren

Variante mit `ogr2ogr` auf vorbereiteten Geofabrik-Daten:

```bash
ogr2ogr \
  -f PostgreSQL PG:"host=localhost dbname=pv_marketing_zh user=postgres password=postgres" \
  data_raw/zurich_streets.gpkg \
  -nln raw.osm_streets_raw \
  -lco GEOMETRY_NAME=geom \
  -nlt MULTILINESTRING
```

## Reihenfolge der Ausfuehrung

1. Rohdaten in `data_raw/` ablegen
2. `.env` erstellen und pruefen
3. SQL-Skripte in dieser Reihenfolge ausfuehren:
   - `sql/01_create_schema.sql`
   - Datenimport per `ogr2ogr` und `\copy`
   - `sql/02_prepare_roofs.sql`
   - `sql/03_prepare_quartiers.sql`
   - `sql/04_aggregate_to_quartiers.sql`
   - `sql/05_export_views.sql`
4. Python-Analyse starten:

```bash
python src/targeting_analysis.py
```

5. Ergebnislayer in QGIS laden:
   - `mart.quartier_targeting_results`
   - `mart.top_roofs_for_campaign`
   - optional `mart.street_segments_priority`

## Erwartete Outputs

### In PostGIS

- `core.roofs_top_candidates`
- `core.quartiers_enriched`
- `mart.quartier_roof_metrics`
- `mart.quartier_targeting_results`
- `mart.top_roofs_for_campaign`
- optional `mart.street_segments_priority`

### In `exports/`

- `quartier_targeting_results.gpkg`
- `quartier_targeting_results.csv`
- `top_roofs_for_campaign.gpkg`

## QGIS-Hinweise

- Quartiere als Choroplethenkarte auf Basis von `marketing_targeting_score`
- 3 Klassen fuer `score_class`: niedrig, mittel, hoch
- Top-5-Quartiere mit Labels fuer Quartiername und Score
- Top-Daecher als Punkt- oder Polygonoverlay in neutralem Gelb/Orange
- Basemap zurueckhaltend halten, damit die Priorisierungslogik im Vordergrund bleibt

Details stehen in `qgis/README.md`.

## Pitch-relevante Kernaussagen

- Nicht jedes sonnige Dach ist ein guter Vertriebslead.
- Die Kombination aus Dachpotenzial und Demografie liefert eine vertriebsnaehere Priorisierung.
- Das Ergebnis ist keine Prognose fuer Abschluesse, sondern eine datenbasierte Entscheidungshilfe fuer Gebietsselektion.
- Quartiere mit vielen ertragsstarken Daechern und hoher Kaufkraft sind die erste Prioritaet fuer Direktmarketing.

## Wichtige Annahmen

- Die exakten Feldnamen des BFE-Datensatzes und der demografischen Dateien koennen lokal abweichen.
- Alle SQL- und Python-Schritte verwenden deshalb sprechende Platzhalter und klar kommentierte Mapping-Stellen.
- Vor dem ersten produktiven Lauf muessen Spaltennamen fuer:
  - Eignungsklasse
  - Dachflaeche
  - Stromertrag
  - Quartier-ID
  - Einkommen
  - optionale Eigentums- oder Wohnstrukturmerkmale
  an die realen Quelldaten angepasst werden.

## Realistische Projektgrenzen

- Kein Machine Learning
- Keine Web-App
- Keine Cloud-Architektur
- Kein Anspruch auf exakte Absatzprognose

Der Prototyp ist bewusst als nachvollziehbares Hochschulprojekt konzipiert: fachlich plausibel, technisch sauber und in einer studentischen Gruppenarbeit realistisch umsetzbar.
