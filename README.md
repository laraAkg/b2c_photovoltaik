# B2C Photovoltaik Geomarketing

Streamlit-Prototyp fuer ein Geomarketing-Projekt in Zuerich. Die App kombiniert technisches PV-Potenzial mit Quartierdaten und hilft, Quartiere, Strassen und einzelne Adressen fuer Photovoltaik-Marketing zu priorisieren.

## Was die App zeigt

- dynamische Quartier-Rankings nach PV-Ertrag, guten Daechern, Einkommen und Eigentumsquote
- Top-Strassen fuer lokale Kampagnen und Aussendienstplanung
- priorisierte Adressen als operative Lead-Ebene
- interaktive Karte der Quartier-Scores
- CSV-Downloads fuer die wichtigsten Tabellen

## Projektstruktur

```text
b2c_photovoltaik/
├── app.py                  # Streamlit-Frontend
├── requirements.txt        # Python-Abhaengigkeiten
├── requirements-analysis.txt
├── .env.example            # Beispiel fuer lokale DB-Konfiguration
├── src/
│   └── geomarketing_app/
│       └── data.py         # Datenbankabfragen, Scoring und Datenaufbereitung
├── scripts/
│   ├── import_geomarketing_dump.ps1
│   ├── recompute_targeting_score.py
│   └── start_app_windows.ps1
└── docs/
    └── qgis.md             # Hinweise fuer QGIS-Visualisierung
```

Nicht ins Git gehoeren lokale Datenbank-Dumps, Rohdaten, virtuelle Umgebungen und `.env`-Dateien. Das ist in `.gitignore` abgedeckt.

## Voraussetzungen

- Python 3.10 oder neuer
- PostgreSQL mit PostGIS
- ein importierter Datenbank-Dump mit den erwarteten `mart`-Views

Die App erwartet standardmaessig diese Tabellen/Views:

- `mart.quartier_targeting_results_map`
- `mart.strassen_mit_pv`
- `mart.adressen_mit_pv`

## Installation auf Windows

```powershell
git clone https://github.com/YanickMoos/b2c_photovoltaik.git
cd b2c_photovoltaik
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Falls PowerShell die Aktivierung blockiert:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Danach ein neues Terminal oeffnen und die Aktivierung erneut ausfuehren.

Optionale Analyse- und Notebook-Pakete sind getrennt, damit die Webapp unter Windows schneller und stabiler installiert:

```powershell
pip install -r requirements-analysis.txt
```

## Datenbank einrichten

Wenn PostgreSQL auf dem Standardport `5432` laeuft:

```powershell
createdb -p 5432 geomarketing
psql -p 5432 -d geomarketing -c "CREATE EXTENSION IF NOT EXISTS postgis;"
pg_restore -p 5432 -d geomarketing .\geomarketing.dump
```

Wenn PostgreSQL auf Port `5433` laeuft, zum Beispiel bei Postgres.app auf Mac:

```powershell
createdb -p 5433 geomarketing
psql -p 5433 -d geomarketing -c "CREATE EXTENSION IF NOT EXISTS postgis;"
pg_restore -p 5433 -d geomarketing .\geomarketing.dump
```

## Datenbankverbindung konfigurieren

Optional `.env.example` nach `.env` kopieren und anpassen:

```powershell
copy .env.example .env
```

Die wichtigste Variable ist:

```text
GEOMARKETING_DB_URL=postgresql+psycopg2://postgres@localhost:5432/geomarketing
```

Wenn keine Variable gesetzt ist, nutzt die App einen lokalen Standardwert.

## App starten

```powershell
streamlit run app.py
```

Danach oeffnet Streamlit die App im Browser, normalerweise unter:

```text
http://localhost:8501
```

## Typische Probleme

### Schneller Start unter Windows

Alternativ kann das Hilfsskript Setup und Start uebernehmen:

```powershell
.\scripts\start_app_windows.ps1
```

### Dump importieren

Wenn `geomarketing.dump` z. B. im Downloads-Ordner liegt:

```powershell
.\scripts\import_geomarketing_dump.ps1 -DumpPath "$env:USERPROFILE\Downloads\geomarketing.dump" -Port 5432
```

### `CREATE EXTENSION postgis` funktioniert nicht

PostGIS ist noch nicht installiert. Unter Windows kann es ueber den PostgreSQL Stack Builder nachinstalliert werden:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\stackbuilder.exe"
```

### Verbindung zur Datenbank schlaegt fehl

Pruefe Port, Benutzername und Datenbankname:

```powershell
psql -p 5432 -d geomarketing
```

Falls deine lokale Installation einen anderen Port verwendet, passe `GEOMARKETING_DB_URL` entsprechend an.

### Dump-Datei ist gross

`geomarketing.dump` nicht ins Git pushen. Besser ueber Google Drive, OneDrive, Dropbox oder WeTransfer teilen.

## Fachliche Idee

Nicht jedes sonnige Dach ist automatisch ein guter Vertriebslead. Der Prototyp verbindet technische Solarpotenziale mit demografischer Attraktivitaet und macht daraus eine nachvollziehbare Priorisierung fuer B2C-Marketing.
