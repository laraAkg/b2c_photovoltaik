param(
    [Parameter(Mandatory = $true)]
    [string]$DumpPath,

    [int]$Port = 5432,
    [string]$Database = "geomarketing",
    [string]$User = "postgres"
)

$ErrorActionPreference = "Stop"

$pgBin = "C:\Program Files\PostgreSQL\18\bin"
$createdb = Join-Path $pgBin "createdb.exe"
$psql = Join-Path $pgBin "psql.exe"
$pgRestore = Join-Path $pgBin "pg_restore.exe"

foreach ($tool in @($createdb, $psql, $pgRestore)) {
    if (-not (Test-Path $tool)) {
        throw "PostgreSQL Tool wurde nicht gefunden: $tool"
    }
}

if (-not (Test-Path $DumpPath)) {
    throw "Dump-Datei wurde nicht gefunden: $DumpPath"
}

Write-Host "Erstelle Datenbank $Database auf Port $Port ..."
$exists = & $psql -h localhost -p $Port -U $User -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '$Database';"

if ($LASTEXITCODE -ne 0) {
    throw "Konnte Datenbankliste nicht pruefen."
}

if ($null -ne $exists -and $exists.Trim() -eq "1") {
    Write-Host "Datenbank $Database existiert bereits. Sie wird nicht geloescht oder ueberschrieben."
} else {
    & $createdb -h localhost -p $Port -U $User $Database
}

Write-Host "Aktiviere PostGIS Extension ..."
& $psql -h localhost -p $Port -U $User -d $Database -c "CREATE EXTENSION IF NOT EXISTS postgis;"

Write-Host "Importiere Dump ..."
& $pgRestore -h localhost -p $Port -U $User -d $Database $DumpPath

Write-Host "Fertig: $Database wurde importiert."
