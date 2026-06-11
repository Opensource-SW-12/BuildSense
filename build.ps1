# BuildSense Windows 빌드 스크립트 (onedir)
# 사용법: powershell -ExecutionPolicy Bypass -File build.ps1

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root

Write-Host "[1/4] 이전 빌드 산출물 정리" -ForegroundColor Cyan
Remove-Item -Recurse -Force "build" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "dist" -ErrorAction SilentlyContinue

Write-Host "[2/4] PyInstaller 빌드 실행" -ForegroundColor Cyan
python -m PyInstaller BuildSense.spec --clean --noconfirm
if ($LASTEXITCODE -ne 0) { throw "PyInstaller 빌드 실패 (exit $LASTEXITCODE)" }

$distApp = Join-Path $root "dist\BuildSense"
$distData = Join-Path $distApp "data"

Write-Host "[3/4] 데이터 파일 복사" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $distData | Out-Null
Copy-Item -Recurse -Force "data\specs" $distData
Copy-Item -Force "data\process_categories.json" $distData
Copy-Item -Force "data\process_path_overrides.json" $distData
Copy-Item -Force "data\.gitkeep" $distData

Write-Host "[4/4] .env.example 복사" -ForegroundColor Cyan
Copy-Item -Force ".env.example" $distApp

Write-Host "빌드 완료: $distApp\BuildSense.exe" -ForegroundColor Green
