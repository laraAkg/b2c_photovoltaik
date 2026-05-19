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
# B2C Photovoltaik Geomarketing

Dieses Projekt ist eine Streamlit-App für ein Geomarketing-Szenario in Zürich. Die App verbindet Photovoltaik-Potenzial mit Quartier-, Strassen- und Adressdaten. Ziel ist es, geeignete Gebiete für B2C-Photovoltaik-Marketing nachvollziehbar zu priorisieren.

Diese Anleitung ist so geschrieben, dass eine andere Person das Projekt lokal reproduzieren und starten kann.

## Kurzüberblick

Die App zeigt:

- ein dynamisches Ranking von Quartieren
- eine Bewertung nach PV-Ertrag, guten Dächern, Einkommen und Eigentumsquote
- Top-Strassen für Kampagnen und Außendienstplanung
- priorisierte Adressen als operative Lead-Liste
- eine interaktive Karte der Quartier-Scores
- CSV-Downloads der wichtigsten Tabellen

Der technische Ablauf ist:

```text
Repository + geomarketing.dump
        -> PostgreSQL/PostGIS-Datenbank
        -> Streamlit-App
        -> Browser-Dashboard
```

## Wichtig Für Die Reproduzierbarkeit

Für eine vollständige Reproduktion werden zwei Dinge benötigt:

1. Dieses Repository
2. Die Datenbank-Datei `geomarketing.dump`

Die Datei `geomarketing.dump` ist ein Export der PostgreSQL/PostGIS-Datenbank. Sie enthält die Daten, Tabellen und Geometrien, welche die App benötigt.

Ohne `geomarketing.dump` kann die App zwar installiert und gestartet werden, aber sie kann keine fachlichen Daten anzeigen.

Nach dem Import müssen mindestens diese Tabellen vorhanden sein:

```text
mart.quartier_targeting_results_map
mart.strassen_mit_pv
mart.adressen_mit_pv
```

## Datenbereitstellung Von `geomarketing.dump`

Damit eine neue Person das Projekt ohne Rueckfragen starten kann, sollte die Bereitstellung der Dump-Datei klar dokumentiert sein.

Empfohlene Mindestangaben:

- **Bezugsquelle**: z. B. Moodle, OneDrive/SharePoint oder ein interner Kursordner
- **Dateiname**: `geomarketing.dump`
- **Version/Stand**: z. B. `Stand 2026-05-15` oder Tag des Exports
- **Erwartete Groesse**: grober Richtwert in MB/GB
- **Kontakt**: wer die Datei bereitstellt, falls der Link nicht mehr gueltig ist

Beispiel-Text zum Ersetzen:

```text
Bezugsquelle: <LINK_EINFUEGEN>
Stand: <YYYY-MM-DD>
Dateiname: geomarketing.dump
Kontakt: <NAME/EMAIL_EINFUEGEN>
```

Optional kann zusaetzlich eine SHA256-Pruefsumme dokumentiert werden, um Datei-Integritaet zu pruefen.

## Projektstruktur

```text
b2c_photovoltaik/
|-- app.py                              # Streamlit-App
|-- requirements.txt                    # Python-Pakete für die App
|-- requirements-analysis.txt           # optionale Pakete für Analyse/Notebook
|-- .env.example                        # Vorlage für die Datenbankverbindung
|-- src/
|   `-- geomarketing_app/
|       `-- data.py                     # Datenbankabfragen und Scoring
|-- scripts/
|   |-- import_geomarketing_dump.ps1    # optionales Import-Skript für Windows
|   |-- recompute_targeting_score.py    # optionaler Recompute des Scores
|   `-- start_app_windows.ps1           # optionaler Starthelfer für Windows
`-- docs/
    `-- qgis.md                         # Hinweise für QGIS
```

## Methodik Und Scoring-Logik (Kurz)

Die Quartierpriorisierung basiert auf vier fachlichen Komponenten:

- PV-Potenzial ueber `sum_stromertrag`
- Anzahl geeigneter Daecher ueber `anzahl_gute_daecher`
- Kaufkraft ueber `median_income`
- Eigentumsnaehe ueber `eigentumsquote`

Im App-Flow werden diese Kennzahlen je Quartier min-max normalisiert und mit Strategiegeweichten kombiniert. Die Standardstrategien (`Balanced`, `Technical`, `Premium`, `Ownership-focused`) sind in `src/geomarketing_app/data.py` als `STRATEGY_WEIGHTS` hinterlegt.

Die Berechnung des dynamischen Scores erfolgt ueber `compute_quartier_scores()` in `src/geomarketing_app/data.py`. Fuer Szenariorechnungen kann der persistierte Datenbank-Score mit `scripts/recompute_targeting_score.py` neu geschrieben werden.

Hinweis zur Interpretation: Ein hoher Score bedeutet relative Prioritaet innerhalb des geladenen Datenstands, nicht automatisch technische Machbarkeit einzelner Gebaeude.

## Voraussetzungen

Für Windows werden benötigt:

- Git
- Python 3.10 oder neuer
- PostgreSQL 18
- PostGIS für PostgreSQL 18
- die Datei `geomarketing.dump`

Die Anleitung nutzt PowerShell. Wenn PostgreSQL in einer anderen Version installiert wurde, muss der Pfad `C:\Program Files\PostgreSQL\18\bin` entsprechend angepasst werden.

## Schnellstart (Fuer Erfahrene Nutzer)

Wenn Python, PostgreSQL und PostGIS bereits installiert sind und `geomarketing.dump` vorliegt, reicht oft dieser Kurzweg:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$PgBin = "C:\Program Files\PostgreSQL\18\bin"
$DumpPath = "C:\Pfad\zu\geomarketing.dump"
& "$PgBin\createdb.exe" -U postgres -p 5432 geomarketing
& "$PgBin\psql.exe" -U postgres -p 5432 -d geomarketing -c "CREATE EXTENSION IF NOT EXISTS postgis;"
& "$PgBin\pg_restore.exe" --no-owner -U postgres -p 5432 -d geomarketing "$DumpPath"
copy .env.example .env
streamlit run app.py
```

Alternative mit den vorhandenen Skripten:

- Import: `.\scripts\import_geomarketing_dump.ps1 -DumpPath "C:\Pfad\zu\geomarketing.dump"`
- App-Start: `.\scripts\start_app_windows.ps1`

Wichtig zur Konsistenz:

- `import_geomarketing_dump.ps1` nutzt standardmaessig `pg_restore` ohne `--no-owner`. Falls beim Skriptlauf ein Rollenfehler wie `Rolle "lara" existiert nicht` auftritt, den manuellen Import aus Schritt 6 mit `--no-owner` verwenden.
- `start_app_windows.ps1` referenziert aktuell `C:\Program Files\Python312\python.exe`. Wenn Python bei dir anders installiert ist, den manuellen Weg aus Schritt 2 + Schritt 9 verwenden oder den Skriptpfad lokal anpassen.

## 1. Repository Klonen Oder Öffnen

Wenn das Repository noch nicht lokal vorhanden ist:

```powershell
git clone https://github.com/laraAkg/b2c_photovoltaik.git
cd b2c_photovoltaik
```

Wenn das Repository bereits lokal vorhanden ist, in den Projektordner wechseln:

```powershell
cd "C:\Pfad\zum\Projekt\b2c_photovoltaik"
```

Wichtig: Bei Pfaden mit Leerzeichen müssen Anführungszeichen verwendet werden.

## 2. Python-Umgebung Einrichten

Virtuelle Umgebung erstellen:

```powershell
python -m venv .venv
```

Virtuelle Umgebung aktivieren:

```powershell
.\.venv\Scripts\Activate.ps1
```

Falls PowerShell die Aktivierung blockiert:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Danach PowerShell neu öffnen und die Umgebung erneut aktivieren:

```powershell
.\.venv\Scripts\Activate.ps1
```

Python-Pakete installieren:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Optional können zusätzliche Analysepakete installiert werden:

```powershell
pip install -r requirements-analysis.txt
```

Für den App-Start reicht `requirements.txt`.

## 3. PostgreSQL Und PostGIS Installieren

Installiere PostgreSQL 18 für Windows. Während der Installation wird ein Passwort für den Benutzer `postgres` gesetzt. Dieses Passwort wird später in der Datei `.env` benötigt.

Danach PostGIS installieren:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\stackbuilder.exe"
```

Im Stack Builder:

1. PostgreSQL 18 auswählen.
2. Kategorie `Spatial Extensions` öffnen.
3. `PostGIS` auswählen und installieren.

Wenn `psql` später nicht direkt gefunden wird, ist das normal. Dann wird in dieser Anleitung der vollständige PostgreSQL-Pfad verwendet.

## 4. Wichtige Pfade Als Variablen Setzen

Damit die Befehle einfacher kopiert werden können, werden zwei Variablen gesetzt.

Im Projektordner in PowerShell:

```powershell
$PgBin = "C:\Program Files\PostgreSQL\18\bin"
$DumpPath = "C:\Pfad\zu\geomarketing.dump"
```

`$DumpPath` muss auf den tatsächlichen Speicherort der Datei `geomarketing.dump` zeigen.

Beispiel:

```powershell
$DumpPath = "C:\Users\Public\Downloads\geomarketing.dump"
```

## 5. Datenbank Erstellen

Die App erwartet eine PostgreSQL-Datenbank mit dem Namen `geomarketing`.

```powershell
& "$PgBin\createdb.exe" -U postgres -p 5432 geomarketing
```

Wenn die Meldung erscheint, dass die Datenbank bereits existiert, ist das nicht schlimm. Dann kann der Schritt übersprungen werden.

PostGIS in der Datenbank aktivieren:

```powershell
& "$PgBin\psql.exe" -U postgres -p 5432 -d geomarketing -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

PostGIS prüfen:

```powershell
& "$PgBin\psql.exe" -U postgres -p 5432 -d geomarketing -c "SELECT PostGIS_Version();"
```

Erwartet ist eine Ausgabe mit einer PostGIS-Version, zum Beispiel:

```text
3.6 USE_GEOS=1 USE_PROJ=1 USE_STATS=1
```

## 6. Datenbank-Dump Importieren

Jetzt wird `geomarketing.dump` in die Datenbank `geomarketing` importiert.

```powershell
& "$PgBin\pg_restore.exe" --no-owner -U postgres -p 5432 -d geomarketing "$DumpPath"
```

Warum `--no-owner`?

Der Dump kann auf einem anderen Computer mit einem anderen Datenbankbenutzer erstellt worden sein. Ohne `--no-owner` können Fehlermeldungen wie diese auftreten:

```text
Rolle "lara" existiert nicht
```

Mit `--no-owner` werden die Daten trotzdem in die lokale Datenbank importiert.

Wenn der Import wegen bereits vorhandener Tabellen fehlschlägt, kann die Datenbank neu erstellt werden. Achtung: Das löscht die lokale Datenbank `geomarketing`.

```powershell
& "$PgBin\dropdb.exe" -U postgres -p 5432 geomarketing
& "$PgBin\createdb.exe" -U postgres -p 5432 geomarketing
& "$PgBin\psql.exe" -U postgres -p 5432 -d geomarketing -c "CREATE EXTENSION IF NOT EXISTS postgis;"
& "$PgBin\pg_restore.exe" --no-owner -U postgres -p 5432 -d geomarketing "$DumpPath"
```

## 7. Import Prüfen

Nach dem Import prüfen, ob die Tabellen vorhanden sind:

```powershell
& "$PgBin\psql.exe" -U postgres -p 5432 -d geomarketing -c "SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema IN ('raw','core','mart') ORDER BY table_schema, table_name;"
```

Für die App müssen mindestens diese drei Tabellen erscheinen:

```text
mart | adressen_mit_pv
mart | quartier_targeting_results_map
mart | strassen_mit_pv
```

Gezielter Check nur für die App-Tabellen:

```powershell
& "$PgBin\psql.exe" -U postgres -p 5432 -d geomarketing -c "SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema = 'mart' AND table_name IN ('quartier_targeting_results_map', 'strassen_mit_pv', 'adressen_mit_pv') ORDER BY table_name;"
```

Optional kann geprüft werden, ob Daten enthalten sind:

```powershell
& "$PgBin\psql.exe" -U postgres -p 5432 -d geomarketing -c "SELECT COUNT(*) FROM mart.quartier_targeting_results_map;"
& "$PgBin\psql.exe" -U postgres -p 5432 -d geomarketing -c "SELECT COUNT(*) FROM mart.strassen_mit_pv;"
& "$PgBin\psql.exe" -U postgres -p 5432 -d geomarketing -c "SELECT COUNT(*) FROM mart.adressen_mit_pv;"
```

Wenn keine `mart`-Tabellen erscheinen, wurde der Dump nicht korrekt importiert oder in die falsche Datenbank importiert.

## 8. Datenbankverbindung Konfigurieren

Die App liest die Datenbankverbindung aus der Datei `.env`.

Vorlage kopieren:

```powershell
copy .env.example .env
```

Danach `.env` öffnen und die Variable `GEOMARKETING_DB_URL` setzen.

Wenn der PostgreSQL-Benutzer `postgres` ein Passwort hat:

```text
GEOMARKETING_DB_URL=postgresql+psycopg2://postgres:DEIN_PASSWORT@localhost:5432/geomarketing
```

Beispiel:

```text
GEOMARKETING_DB_URL=postgresql+psycopg2://postgres:1234@localhost:5432/geomarketing
```

Wenn PostgreSQL lokal ohne Passwort funktioniert:

```text
GEOMARKETING_DB_URL=postgresql+psycopg2://postgres@localhost:5432/geomarketing
```

Wichtig:

- `.env` enthält lokale Zugangsdaten und gehört nicht ins Git.
- `.env.example` ist nur die Vorlage.
- Nach Änderungen an `.env` muss die Streamlit-App neu gestartet werden.

## 9. App Starten

Sicherstellen, dass die virtuelle Umgebung aktiv ist:

```powershell
.\.venv\Scripts\Activate.ps1
```

App starten:

```powershell
streamlit run app.py
```

Streamlit öffnet normalerweise automatisch den Browser. Falls nicht:

```text
http://localhost:8501
```

Wenn die App bereits läuft, zuerst im Terminal mit `Ctrl + C` stoppen und dann erneut starten:

```powershell
streamlit run app.py
```

## Erwartetes Ergebnis

Wenn alles korrekt eingerichtet wurde, erscheint im Browser das Dashboard:

```text
Geomarketing-Tool für Photovoltaik in Zürich
```

Die App sollte Daten laden und folgende Bereiche anzeigen:

- Auswahl der Analyseebene `Quartier`, `Straße` oder `Adresse`
- Strategie-Modus wie `Balanced`, `Technical`, `Premium`, `Ownership-focused` oder `Custom`
- Kennzahlen zu Quartieren, Straßen und Adressen
- Tabellen, Diagramme und Karte
- CSV-Downloads

## Optional: Targeting-Score Neu Berechnen

Der normale App-Start benötigt diesen Schritt nicht.

Das Skript `scripts/recompute_targeting_score.py` kann verwendet werden, wenn der Quartier-Score mit anderen Gewichten neu in die Datenbank geschrieben werden soll.

Das Skript liest:

- `mart.quartier_metrics_full`
- `core.quartiere_plus`

Es schreibt:

- `mart.quartier_targeting_results`
- `mart.quartier_targeting_results_map`

Ausführung:

```powershell
python .\scripts\recompute_targeting_score.py
```

Das Skript fragt vier Gewichte ab. Die Summe muss 100 ergeben:

```text
Gewicht Stromertrag (%)
Gewicht gute Dächer (%)
Gewicht Einkommen (%)
Gewicht Eigentumsquote (%)
```

Danach die App neu starten:

```powershell
streamlit run app.py
```

## Optional: QGIS

Für eine kartografische Auswertung können die Layer aus dem Schema `mart` in QGIS geladen werden.

Details stehen in:

```text
docs/qgis.md
```

Relevante Layer:

- `mart.quartier_targeting_results_map`
- `mart.strassen_mit_pv`
- `mart.adressen_mit_pv`

Empfohlenes Projekt-CRS:

```text
EPSG:2056
```

## Troubleshooting

### `psql` Wird Nicht Gefunden

Fehler:

```text
psql wurde nicht als Name eines Cmdlet erkannt
```

Lösung:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -p 5432
```

Oder den Pfad über die Variable setzen:

```powershell
$PgBin = "C:\Program Files\PostgreSQL\18\bin"
```

### PostGIS Ist Nicht Verfügbar

Fehler:

```text
Erweiterung postgis ist nicht verfügbar
```

Lösung: PostGIS über Stack Builder installieren:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\stackbuilder.exe"
```

Danach erneut:

```powershell
& "$PgBin\psql.exe" -U postgres -p 5432 -d geomarketing -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

### `Rolle lara existiert nicht` Beim Dump-Import

Der Dump wurde mit einem anderen Datenbankbenutzer erstellt. Import mit `--no-owner` ausführen:

```powershell
& "$PgBin\pg_restore.exe" --no-owner -U postgres -p 5432 -d geomarketing "$DumpPath"
```

### App Kann Keine Verbindung Zur Datenbank Herstellen

Prüfen:

1. Läuft PostgreSQL?
2. Existiert die Datenbank `geomarketing`?
3. Ist PostGIS aktiviert?
4. Wurde `geomarketing.dump` importiert?
5. Stimmt `GEOMARKETING_DB_URL` in `.env`?
6. Wurde die App nach Änderung der `.env` neu gestartet?

Direkter Verbindungstest:

```powershell
& "$PgBin\psql.exe" -U postgres -p 5432 -d geomarketing
```

Wenn hier ein Passwort verlangt wird, muss dieses Passwort auch in `.env` stehen:

```text
GEOMARKETING_DB_URL=postgresql+psycopg2://postgres:DEIN_PASSWORT@localhost:5432/geomarketing
```

### App Findet Die Tabellen Nicht

Prüfen:

```powershell
& "$PgBin\psql.exe" -U postgres -p 5432 -d geomarketing -c "SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema = 'mart' AND table_name IN ('quartier_targeting_results_map', 'strassen_mit_pv', 'adressen_mit_pv') ORDER BY table_name;"
```

Wenn nicht alle drei Tabellen erscheinen, wurde der Dump nicht korrekt importiert.

### PowerShell Blockiert Die Virtuelle Umgebung

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Danach PowerShell neu öffnen und erneut:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Komplette Checkliste Für Eine Neue Person

1. Repository klonen.
2. Datei `geomarketing.dump` bereitlegen.
3. Python-Umgebung `.venv` erstellen.
4. `requirements.txt` installieren.
5. PostgreSQL 18 installieren.
6. PostGIS über Stack Builder installieren.
7. `$PgBin` und `$DumpPath` in PowerShell setzen.
8. Datenbank `geomarketing` erstellen.
9. PostGIS in `geomarketing` aktivieren.
10. `geomarketing.dump` mit `pg_restore --no-owner` importieren.
11. Import mit den `mart`-Checks prüfen.
12. `.env.example` nach `.env` kopieren.
13. `GEOMARKETING_DB_URL` in `.env` mit lokalem Passwort anpassen.
14. App mit `streamlit run app.py` starten.
15. Browser unter `http://localhost:8501` öffnen.

Wenn diese Schritte mit derselben Repository-Version und derselben Datei `geomarketing.dump` durchgeführt werden, ist das Projekt lokal reproduzierbar.
