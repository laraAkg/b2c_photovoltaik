# B2C Photovoltaik Geomarketing

Streamlit-App zur Priorisierung von B2C-Photovoltaik-Potenzialen in der Stadt Zürich.
Die Anwendung kombiniert Quartier-, Strassen- und Adressdaten mit PV-relevanten Kennzahlen, um Zielgebiete nachvollziehbar zu ranken.

---

## Inhalt

- [Projektziel](#projektziel)
- [Schnellstart (5-10 Minuten)](#schnellstart-5-10-minuten)
- [Projektstruktur](#projektstruktur)
- [Datenbasis und Reproduzierbarkeit](#datenbasis-und-reproduzierbarkeit)
- [Vollsetup unter Windows (PowerShell)](#vollsetup-unter-windows-powershell)
- [Methodik und Scoring-Logik](#methodik-und-scoring-logik)
- [Hilfsskripte](#hilfsskripte)
- [QGIS (optional)](#qgis-optional)
- [Troubleshooting](#troubleshooting)
- [Reproduzierbarkeits-Checkliste](#reproduzierbarkeits-checkliste)

---

## Projektziel

Die App beantwortet drei operative Fragen:

1. **Welche Quartiere sind insgesamt am attraktivsten?**
2. **Welche Strassen eignen sich fuer Kampagnen und Aussendienst?**
3. **Welche Adressen sind als naechste Leads priorisiert?**

Ergebnisse im Dashboard:

- dynamisches Quartier-Ranking
- Strategiemodi (`Balanced`, `Technical`, `Premium`, `Ownership-focused`, `Custom`)
- Top-Listen auf Strassen- und Adressebene
- interaktive Karte der Quartier-Scores
- CSV-Downloads der wichtigsten Tabellen

Technischer Ablauf:

```text
Repository + geomarketing.dump
        -> PostgreSQL/PostGIS-Datenbank
        -> Streamlit-App
        -> Browser-Dashboard
```

---

## Schnellstart (5-10 Minuten)

Voraussetzung: Python, PostgreSQL + PostGIS und `geomarketing.dump` sind bereits vorhanden.

```powershell
# 1) Repository
git clone https://github.com/laraAkg/b2c_photovoltaik.git
cd b2c_photovoltaik

# 2) Python-Umgebung
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt

# 3) DB-Import
$PgBin = "C:\Program Files\PostgreSQL\18\bin"
$DumpPath = "C:\Pfad\zu\geomarketing.dump"
& "$PgBin\createdb.exe" -U postgres -p 5432 geomarketing
& "$PgBin\psql.exe" -U postgres -p 5432 -d geomarketing -c "CREATE EXTENSION IF NOT EXISTS postgis;"
& "$PgBin\pg_restore.exe" --no-owner -U postgres -p 5432 -d geomarketing "$DumpPath"

# 4) App starten
copy .env.example .env
streamlit run app.py
```

Dann im Browser:

```text
http://localhost:8501
```

---

## Projektstruktur

```text
b2c_photovoltaik/
|-- app.py                              # Streamlit-App
|-- requirements.txt                    # App-Abhaengigkeiten
|-- requirements-analysis.txt           # optionale Analyse-Abhaengigkeiten
|-- .env.example                        # Vorlage fuer DB-Verbindung
|-- src/
|   `-- geomarketing_app/
|       `-- data.py                     # Datenzugriff + Scoring
|-- scripts/
|   |-- import_geomarketing_dump.ps1    # DB-Import-Helfer
|   |-- recompute_targeting_score.py    # Score persistiert neu berechnen
|   `-- start_app_windows.ps1           # App-Start-Helfer
`-- docs/
    `-- qgis.md                         # QGIS-Hinweise
```

---

## Datenbasis und Reproduzierbarkeit

Fuer eine vollstaendige Reproduktion werden benoetigt:

1. dieses Repository
2. die Datei `geomarketing.dump`

### Mindestangaben zur Dump-Datei

Pflege diese Angaben fuer neue Teammitglieder im Projektkontext:

- **Bezugsquelle**: `<LINK_ODER_ORDNER_EINFUEGEN>`
- **Stand/Version**: `<YYYY-MM-DD_ODER_TAG>`
- **Dateiname**: `geomarketing.dump`
- **Kontakt**: `<NAME_ODER_EMAIL>`

Optional:

- erwartete Dateigroesse (MB/GB)
- SHA256-Pruefsumme fuer Integritaetscheck

### Warum die Dump-Datei zwingend ist

Ohne `geomarketing.dump` kann die App starten, aber keine fachlichen Daten anzeigen.
Nach erfolgreichem Import sollten mindestens diese Tabellen existieren:

```text
mart.quartier_targeting_results_map
mart.strassen_mit_pv
mart.adressen_mit_pv
```

---

## Vollsetup unter Windows (PowerShell)

> Die Anleitung ist auf Windows + PowerShell ausgelegt.

### 1) Voraussetzungen

- Git
- Python 3.10 oder neuer
- PostgreSQL 18 (oder kompatibel, Pfade dann anpassen)
- PostGIS fuer PostgreSQL
- `geomarketing.dump`

### 2) Repository oeffnen

```powershell
cd "C:\Pfad\zum\Projekt\b2c_photovoltaik"
```

### 3) Virtuelle Umgebung

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Optional:

```powershell
pip install -r requirements-analysis.txt
```

Falls Activation blockiert wird:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 4) PostGIS aktivieren und Dump importieren

```powershell
$PgBin = "C:\Program Files\PostgreSQL\18\bin"
$DumpPath = "C:\Pfad\zu\geomarketing.dump"

& "$PgBin\createdb.exe" -U postgres -p 5432 geomarketing
& "$PgBin\psql.exe" -U postgres -p 5432 -d geomarketing -c "CREATE EXTENSION IF NOT EXISTS postgis;"
& "$PgBin\pg_restore.exe" --no-owner -U postgres -p 5432 -d geomarketing "$DumpPath"
```

### 5) Import kurz pruefen

```powershell
& "$PgBin\psql.exe" -U postgres -p 5432 -d geomarketing -c "SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema = 'mart' AND table_name IN ('quartier_targeting_results_map', 'strassen_mit_pv', 'adressen_mit_pv') ORDER BY table_name;"
```

### 6) `.env` konfigurieren

```powershell
copy .env.example .env
```

Dann in `.env`:

```text
GEOMARKETING_DB_URL=postgresql+psycopg2://postgres:DEIN_PASSWORT@localhost:5432/geomarketing
```

Oder ohne Passwort:

```text
GEOMARKETING_DB_URL=postgresql+psycopg2://postgres@localhost:5432/geomarketing
```

### 7) App starten

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

---

## Methodik und Scoring-Logik

Die Quartier-Priorisierung nutzt vier Komponenten:

- `sum_stromertrag` (PV-Potenzial)
- `anzahl_gute_daecher` (technische Eignung)
- `median_income` (Kaufkraft)
- `eigentumsquote` (Eigentumsnaehe)

Umsetzung in `src/geomarketing_app/data.py`:

- Standardgewichte je Strategie in `STRATEGY_WEIGHTS`
- Min-Max-Normalisierung ueber `minmax(...)`
- dynamischer Score in `compute_quartier_scores(...)`

Die App arbeitet mit einem relativen Ranking innerhalb des geladenen Datenstands.
Ein hoher Score bedeutet hohe Prioritaet im Vergleich zu anderen Quartieren, nicht automatisch technische Machbarkeit jedes einzelnen Gebaeudes.

Persistenter Recompute in die Datenbank:

```powershell
python .\scripts\recompute_targeting_score.py
```

Dieses Skript liest:

- `mart.quartier_metrics_full`
- `core.quartiere_plus`

und schreibt:

- `mart.quartier_targeting_results`
- `mart.quartier_targeting_results_map`

---

## Hilfsskripte

### `scripts/import_geomarketing_dump.ps1`

```powershell
.\scripts\import_geomarketing_dump.ps1 -DumpPath "C:\Pfad\zu\geomarketing.dump"
```

Hinweis: Das Skript verwendet standardmaessig `pg_restore` ohne `--no-owner`.
Wenn Fehler wie `Rolle "lara" existiert nicht` auftreten, den manuellen Import mit `--no-owner` aus dem Setup oben verwenden.

### `scripts/start_app_windows.ps1`

```powershell
.\scripts\start_app_windows.ps1
```

Hinweis: Das Skript referenziert `C:\Program Files\Python312\python.exe`.
Bei abweichender Python-Installation entweder Skript lokal anpassen oder die manuellen Startschritte nutzen.

---

## QGIS (optional)

Details siehe `docs/qgis.md`.

Relevante Layer:

- `mart.quartier_targeting_results_map`
- `mart.strassen_mit_pv`
- `mart.adressen_mit_pv`

Empfohlenes CRS:

```text
EPSG:2056
```

---

## Troubleshooting

### `psql` wird nicht gefunden

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -p 5432
```

### PostGIS fehlt

PostGIS ueber Stack Builder installieren und danach:

```powershell
& "$PgBin\psql.exe" -U postgres -p 5432 -d geomarketing -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

### Fehler: `Rolle "lara" existiert nicht`

```powershell
& "$PgBin\pg_restore.exe" --no-owner -U postgres -p 5432 -d geomarketing "$DumpPath"
```

### App findet Tabellen nicht

Pruefen, ob alle 3 `mart`-Tabellen vorhanden sind (siehe Import-Check).
Falls nein, Dump erneut in die richtige DB importieren.

### DB-Verbindung fehlgeschlagen

Pruefen:

1. PostgreSQL laeuft
2. DB `geomarketing` existiert
3. PostGIS ist aktiviert
4. Dump wurde importiert
5. `GEOMARKETING_DB_URL` ist korrekt
6. App wurde nach `.env`-Aenderung neu gestartet

---

## Reproduzierbarkeits-Checkliste

1. Repository geklont/geoeffnet
2. `geomarketing.dump` vorhanden
3. `.venv` erstellt und `requirements.txt` installiert
4. PostgreSQL + PostGIS einsatzbereit
5. DB `geomarketing` erstellt und Dump importiert (`--no-owner` bei Bedarf)
6. Importtabellen geprueft (`mart.quartier_targeting_results_map`, `mart.strassen_mit_pv`, `mart.adressen_mit_pv`)
7. `.env` aus `.env.example` erstellt und DB-URL gesetzt
8. App mit `streamlit run app.py` gestartet
9. Dashboard unter `http://localhost:8501` sichtbar

Wenn alle Punkte erfuellt sind, ist das Projekt lokal reproduzierbar.
