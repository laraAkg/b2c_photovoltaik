# B2C Photovoltaik Geomarketing

Streamlit-Prototyp fuer ein Geomarketing-Projekt in Zuerich. Die App kombiniert technisches Photovoltaik-Potenzial mit Quartier-, Strassen- und Adressdaten und priorisiert daraus geeignete Gebiete fuer B2C-Photovoltaik-Marketing.

## Fachliche Motivation

Nicht jedes sonnige Dach ist automatisch ein guter Vertriebslead. Fuer eine sinnvolle Kampagnenplanung werden technische Kriterien wie erwarteter Stromertrag und geeignete Dachflaechen mit demografischen Kriterien wie Einkommen und Eigentumsquote kombiniert. Das Ergebnis ist ein nachvollziehbarer Targeting-Score auf Quartierebene, der in der App bis auf Strassen- und Adressebene genutzt wird.

## Was Die App Zeigt

- dynamische Quartier-Rankings nach PV-Ertrag, guten Daechern, Einkommen und Eigentumsquote
- Top-Strassen fuer lokale Kampagnen und Aussendienstplanung
- priorisierte Adressen als operative Lead-Ebene
- interaktive Karte der Quartier-Scores
- CSV-Downloads fuer die wichtigsten Tabellen

## Architektur Und Projektstruktur

```text
b2c_photovoltaik/
|-- app.py                              # Streamlit-Frontend
|-- requirements.txt                    # Abhaengigkeiten fuer die Webapp
|-- requirements-analysis.txt           # optionale Analyse-/Notebook-Pakete
|-- .env.example                        # Beispiel fuer lokale DB-Konfiguration
|-- src/
|   `-- geomarketing_app/
|       `-- data.py                     # DB-Abfragen, Scoring und Datenaufbereitung
|-- scripts/
|   |-- import_geomarketing_dump.ps1    # Windows-Hilfe fuer Dump-Import
|   |-- recompute_targeting_score.py    # optionaler Recompute des Quartier-Scores
|   `-- start_app_windows.ps1           # Windows-Hilfe fuer Setup und App-Start
`-- docs/
    `-- qgis.md                         # Hinweise fuer QGIS-Visualisierung
```

Der normale Ablauf ist:

```text
geomarketing.dump -> PostgreSQL/PostGIS -> mart-Views -> Streamlit-App
```

Nicht ins Git gehoeren lokale Datenbank-Dumps, Rohdaten, virtuelle Umgebungen und `.env`-Dateien. Das ist in `.gitignore` abgedeckt.

## Voraussetzungen

- Windows mit PowerShell, alternativ ein System mit vergleichbaren Python- und PostgreSQL-Kommandos
- Python 3.10 oder neuer
- PostgreSQL mit aktivierter PostGIS-Erweiterung
- lokaler Datenbank-Dump `geomarketing.dump`
- Git

Die App liest standardmaessig aus der lokalen Datenbank `geomarketing` auf Port `5432`. Das kann ueber `GEOMARKETING_DB_URL` angepasst werden.

## Daten Und Reproduzierbarkeit

Die vollstaendige Reproduzierbarkeit haengt am Datenbank-Dump. Der Dump ist bewusst nicht Teil des Git-Repositories, weil lokale Datenbank-Dumps und Rohdaten nicht versioniert werden sollen.

Erforderliche externe Datei:

```text
geomarketing.dump
```

Noch vom Projektteam zu ergaenzen:

```text
Dump-Bezugsweg: TODO_LINK_ODER_ABGABEORT_EINTRAGEN
Dump-Version: TODO_DUMP_VERSION_ODER_ERSTELLDATUM_EINTRAGEN
```

Ein Bewerter kann das Projekt 1:1 reproduzieren, wenn dieselbe Repository-Version und dieselbe `geomarketing.dump`-Version verwendet werden.

Die Streamlit-App erwartet nach dem Import diese Datenbankobjekte:

- `mart.quartier_targeting_results_map`
- `mart.strassen_mit_pv`
- `mart.adressen_mit_pv`

## Setup Unter Windows

Repository klonen und virtuelle Umgebung vorbereiten:

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

Danach ein neues Terminal oeffnen und die virtuelle Umgebung erneut aktivieren.

Optionale Analyse- und Notebook-Pakete sind getrennt, damit die Webapp schneller und stabiler installiert:

```powershell
pip install -r requirements-analysis.txt
```

## Datenbank Einrichten Und Dump Importieren

Lege `geomarketing.dump` in das Projektverzeichnis oder passe den Pfad im Befehl entsprechend an.

Wenn PostgreSQL auf dem Standardport `5432` laeuft:

```powershell
createdb -p 5432 geomarketing
psql -p 5432 -d geomarketing -c "CREATE EXTENSION IF NOT EXISTS postgis;"
pg_restore -p 5432 -d geomarketing .\geomarketing.dump
```

Wenn PostgreSQL auf Port `5433` laeuft:

```powershell
createdb -p 5433 geomarketing
psql -p 5433 -d geomarketing -c "CREATE EXTENSION IF NOT EXISTS postgis;"
pg_restore -p 5433 -d geomarketing .\geomarketing.dump
```

Alternativ kann unter Windows das Import-Skript verwendet werden:

```powershell
.\scripts\import_geomarketing_dump.ps1 -DumpPath "$env:USERPROFILE\Downloads\geomarketing.dump" -Port 5432
```

Hinweis: Das Skript erwartet PostgreSQL-Tools unter `C:\Program Files\PostgreSQL\18\bin`. Falls PostgreSQL anders installiert wurde, muss der Pfad im Skript angepasst oder der manuelle Import oben verwendet werden.

## Datenbankverbindung Konfigurieren

Die App nutzt ohne weitere Konfiguration diesen Standardwert:

```text
GEOMARKETING_DB_URL=postgresql+psycopg2://postgres@localhost:5432/geomarketing
```

Falls Benutzername, Passwort, Port oder Datenbankname abweichen, `.env.example` nach `.env` kopieren und anpassen:

```powershell
copy .env.example .env
```

Beispiel mit Passwort:

```text
GEOMARKETING_DB_URL=postgresql+psycopg2://postgres:DEIN_PASSWORT@localhost:5432/geomarketing
```

## Validierung Nach Dem Import

Pruefe zuerst, ob die Verbindung zur Datenbank funktioniert:

```powershell
psql -p 5432 -d geomarketing
```

Pruefe danach, ob die fuer die App benoetigten Objekte vorhanden sind:

```powershell
psql -p 5432 -d geomarketing -c "SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema = 'mart' AND table_name IN ('quartier_targeting_results_map', 'strassen_mit_pv', 'adressen_mit_pv') ORDER BY table_name;"
```

Erwartet werden drei Zeilen:

```text
mart | adressen_mit_pv
mart | quartier_targeting_results_map
mart | strassen_mit_pv
```

Optionaler Inhaltscheck:

```powershell
psql -p 5432 -d geomarketing -c "SELECT COUNT(*) FROM mart.quartier_targeting_results_map;"
psql -p 5432 -d geomarketing -c "SELECT COUNT(*) FROM mart.strassen_mit_pv;"
psql -p 5432 -d geomarketing -c "SELECT COUNT(*) FROM mart.adressen_mit_pv;"
```

Wenn diese Befehle Fehler liefern, ist der Dump nicht korrekt importiert oder die Verbindung zeigt auf eine andere Datenbank.

## App Starten

Mit aktivierter virtueller Umgebung:

```powershell
streamlit run app.py
```

Danach oeffnet Streamlit die App im Browser, normalerweise unter:

```text
http://localhost:8501
```

Unter Windows kann alternativ das Start-Skript verwendet werden:

```powershell
.\scripts\start_app_windows.ps1
```

Hinweis: Das Skript erwartet Python unter `C:\Program Files\Python312\python.exe`. Falls Python anders installiert wurde, muss der Pfad im Skript angepasst oder der manuelle Start oben verwendet werden.

## Optional: Targeting-Score Neu Berechnen

Der normale App-Start benoetigt diesen Schritt nicht, wenn der Dump bereits die erwarteten `mart`-Objekte enthaelt.

Das Skript `scripts/recompute_targeting_score.py` kann den Quartier-Score mit eigenen Gewichten neu berechnen. Es liest:

- `mart.quartier_metrics_full`
- `core.quartiere_plus`

Es schreibt danach:

- `mart.quartier_targeting_results`
- `mart.quartier_targeting_results_map`

Ausfuehrung:

```powershell
python .\scripts\recompute_targeting_score.py
```

Das Skript fragt interaktiv vier Gewichte ab. Die Summe muss 100 ergeben:

```text
Gewicht Stromertrag (%)
Gewicht gute Daecher (%)
Gewicht Einkommen (%)
Gewicht Eigentumsquote (%)
```

Nach dem Recompute kann die App erneut mit `streamlit run app.py` gestartet werden.

## Optional: QGIS-Auswertung

Fuer eine kartografische Auswertung koennen die Layer aus dem Schema `mart` in QGIS geladen werden. Details stehen in `docs/qgis.md`.

Relevante Layer:

- `mart.quartier_targeting_results_map`
- `mart.strassen_mit_pv`
- `mart.adressen_mit_pv`

Empfohlenes Projekt-CRS: `EPSG:2056`.

## Typische Probleme

### PowerShell blockiert die virtuelle Umgebung

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Danach PowerShell neu oeffnen und `.\.venv\Scripts\Activate.ps1` erneut ausfuehren.

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

Falls die lokale Installation einen anderen Port verwendet, muss `GEOMARKETING_DB_URL` in `.env` angepasst werden.

### `pg_restore`, `psql` Oder `createdb` Werden Nicht Gefunden

Die PostgreSQL-Binaries sind nicht im `PATH` oder PostgreSQL wurde an einem anderen Ort installiert. Entweder den vollen Pfad verwenden oder den Pfad im Import-Skript anpassen.

### Dump-Datei Fehlt Oder Ist Zu Gross Fuer Git

`geomarketing.dump` nicht ins Git pushen. Fuer die Bewertung muss der Dump extern bereitgestellt werden, z. B. ueber OneDrive, Google Drive, Dropbox oder die Abgabeplattform.

## Hinweise Fuer Bewerter

Fuer eine reproduzierbare Ausfuehrung bitte diese Reihenfolge verwenden:

1. Repository klonen.
2. `geomarketing.dump` aus der Abgabe beziehen und lokal ablegen.
3. Python-Umgebung installieren.
4. PostgreSQL/PostGIS-Datenbank erstellen und Dump importieren.
5. Mit den `psql`-Checks pruefen, ob die drei `mart`-Objekte vorhanden sind.
6. App mit `streamlit run app.py` starten.

Wenn ein Schritt fehlschlaegt, sind meist Port, Datenbank-URL, PostgreSQL-Pfad oder eine abweichende Dump-Version die Ursache.
