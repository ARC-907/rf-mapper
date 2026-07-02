# Fetch the optional MiDaS depth model into weights/model_small.onnx.
# The app runs without it; depth inference stays disabled until present.
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$dest = Join-Path $repoRoot "weights\model_small.onnx"
$url = "https://github.com/isl-org/MiDaS/releases/download/v2_1/model-small.onnx"

if (Test-Path $dest) {
    Write-Host "Model already present at $dest"
    exit 0
}

New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null
Write-Host "Downloading MiDaS small model (~64 MB) from $url ..."
Invoke-WebRequest -Uri $url -OutFile $dest
Write-Host "Saved to $dest"
