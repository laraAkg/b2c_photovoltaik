# QGIS-Setup

## Ziel-Layer

Im aktuellen Datenbank-Dump sind diese Layer fuer QGIS relevant:

- `mart.quartier_targeting_results_map`
- `mart.strassen_mit_pv`
- `mart.adressen_mit_pv`

## Empfohlene Kartenlogik

### 1. Hauptkarte

- Layer: `mart.quartier_targeting_results_map`
- Stil: Choroplethenkarte nach `targeting_score`
- Klassierung: 3 bis 5 Klassen, z. B. Quantile oder Natural Breaks
- Farbidee:
  - niedrig: hellgrau
  - mittel: warmes Gelb
  - hoch: kraeftiges Orange bis Rot

### 2. Erklaerungsebene fuer das Potenzial

- Layer: `mart.strassen_mit_pv`
- Darstellung: sortierte Tabellen-/Diagrammansicht nach `sum_stromertrag`
- Zweck: operative Priorisierung von Strassen fuer Kampagnen oder Aussendienst

### 3. Optionale operative Ebene

- Layer: `mart.adressen_mit_pv`
- Darstellung: Punkt-/Adressliste, gefiltert nach Quartier oder Strasse
- Zweck: konkrete Lead-Liste fuer die Umsetzung

## Labels

- Nur Top-5-Quartiere labeln
- Labelinhalt:
  - `qname`
  - `targeting_score`

Beispiel:

```text
Wiedikon
Score: 82.4
```

## Layout fuer einen 10-Minuten-Pitch

- Ein Hauptlayout mit Titel, Karte, Legende und 3 Kernaussagen
- Kleine Tabelle rechts oder unten mit Top-5-Quartieren
- Keine ueberladene Basemap
- Nordpfeil und Massstab nur dezent, nicht dominant

## Gestaltungsprinzip

Die Karte soll wie ein Vertriebstool wirken:

- klare Priorisierung
- wenig visuelles Rauschen
- Fokus auf Entscheidung, nicht auf Rohdaten

## Praktischer Import in QGIS

1. PostGIS-Verbindung zur Datenbank `geomarketing` anlegen
2. Layer aus Schema `mart` laden
3. Projekt-CRS auf `EPSG:2056` setzen
4. Stil und Labels gemass obiger Logik anwenden
