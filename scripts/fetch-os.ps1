# Download official Octatrack OS 1.40C (your own copy from Elektron).
# Usage:  powershell -ExecutionPolicy Bypass -File scripts/fetch-os.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Dl = Join-Path $Root "downloads"
$Extracted = Join-Path $Dl "extracted"
$ZipUrl = "https://www.elektron.se/wp-content/uploads/2025/03/OCTATRACK_OS1.40C_dist.zip"
$Zip = Join-Path $Dl "OCTATRACK_OS1.40C_dist.zip"

New-Item -ItemType Directory -Force -Path $Dl | Out-Null
New-Item -ItemType Directory -Force -Path $Extracted | Out-Null

Write-Host "[fetch] downloading OS 1.40C ..."
Invoke-WebRequest -Uri $ZipUrl -OutFile $Zip -UseBasicParsing

$hash = Get-FileHash -Path $Zip -Algorithm SHA256
Write-Host "[fetch] ZIP sha256: $($hash.Hash)"

Write-Host "[fetch] extracting ..."
Expand-Archive -Path $Zip -DestinationPath $Extracted -Force

Write-Host "[fetch] firmware files:"
Get-ChildItem -Path $Extracted -Recurse -Include *.bin,*.syx | ForEach-Object { $_.FullName }

Write-Host ""
Write-Host "[fetch] done. Next:"
Write-Host "  python tools/extract_main_os.py"
