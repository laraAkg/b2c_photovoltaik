# QGIS-Setup

## Ziel-Layer

In QGIS sollen mindestens drei Ebenen verwendet werden:

- `mart.quartier_targeting_results`
- `mart.top_roofs_for_campaign`
- optional `mart.street_segments_priority`

## Empfohlene Kartenlogik

### 1. Hauptkarte

- Layer: `mart.quartier_targeting_results`
- Stil: Choroplethenkarte nach `marketing_targeting_score_100`
- Klassierung: `Niedrig`, `Mittel`, `Hoch`
- Farbidee:
  - niedrig: hellgrau
  - mittel: warmes Gelb
  - hoch: kraeftiges Orange bis Rot

### 2. Erklaerungsebene fuer das Potenzial

- Layer: `mart.top_roofs_for_campaign`
- Darstellung: duenne Polygonumrisse oder transparente Flaechen
- Farbe: Gold / Orange
- Zweck: zeigen, dass hohe Quartierscores auf realen Dachclustern beruhen

### 3. Optionale operative Ebene

- Layer: `mart.street_segments_priority`
- Darstellung: abgestufte Linienbreite nach `nearby_top_roofs`
- Zweck: moegliche Aussendienst- oder Flyer-Routen veranschaulichen

## Labels

- Nur Top-5-Quartiere labeln
- Labelinhalt:
  - `quartier_name`
  - `marketing_targeting_score_100`

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

1. PostGIS-Verbindung zur Datenbank `pv_marketing_zh` anlegen
2. Layer aus Schema `mart` laden
3. Projekt-CRS auf `EPSG:2056` setzen
4. Stil und Labels gemass obiger Logik anwenden
