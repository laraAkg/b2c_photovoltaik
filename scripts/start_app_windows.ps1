param(
    [int]$Port = 8501
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$python = "C:\Program Files\Python312\python.exe"
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"

Push-Location $repoRoot

if (-not (Test-Path $venvPython)) {
    if (-not (Test-Path $python)) {
        throw "Python wurde nicht gefunden: $python"
    }

    & $python -m venv .venv
}

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements.txt
& $venvPython -m streamlit run app.py --server.port $Port

Pop-Location
