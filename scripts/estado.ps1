<#
.SYNOPSIS
    Estado de Whetzy (GitHub, Railway, Cloudflare y el repo) sin pedírselo a una sesión.

.DESCRIPTION
    Envoltorio de scripts/estado.py para el PC del dueño. Solo LEE: no escribe en
    ningún servicio ni en el repo. Guarda el informe fuera del proyecto, en
    %LOCALAPPDATA%\whetzy-cache\estado (OneDrive con Controlled Folder Access bloquea
    escribir dentro; ver CLAUDE.md), y compara cada ejecución con la anterior.

    Credenciales (opcionales; sin ellas esa parte sale «sin leer»):
      GITHUB_TOKEN           si falta, usa `gh auth token`
      RAILWAY_PROJECT_TOKEN  token de proyecto del entorno production (último despliegue)

    Documentación: docs/ESTADO_AUTOMATICO.md

.EXAMPLE
    pwsh scripts/estado.ps1 -Abrir
    pwsh scripts/estado.ps1 -Registrar -CadaHoras 3     # tarea programada de Windows
    pwsh scripts/estado.ps1 -Quitar                      # borra esa tarea
#>
param(
    [switch]$Abrir,
    [switch]$Registrar,
    [ValidateRange(1, 24)][int]$CadaHoras = 3,
    [switch]$Quitar,
    [switch]$SinRepo
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
$NombreTarea = 'Whetzy estado'
$Raiz = Split-Path $PSScriptRoot -Parent

if ($Registrar -or $Quitar) {
    if (-not $IsWindows -and $PSVersionTable.PSEdition -eq 'Core') {
        throw 'La tarea programada solo existe en Windows (Programador de tareas).'
    }
    if ($Quitar) {
        Unregister-ScheduledTask -TaskName $NombreTarea -Confirm:$false
        Write-Host "Tarea «$NombreTarea» eliminada."
        return
    }
    $shell = if (Get-Command pwsh -ErrorAction SilentlyContinue) { 'pwsh.exe' } else { 'powershell.exe' }
    $accion = New-ScheduledTaskAction -Execute $shell `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -WorkingDirectory $Raiz
    $disparador = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
        -RepetitionInterval (New-TimeSpan -Hours $CadaHoras)
    $ajustes = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
    Register-ScheduledTask -TaskName $NombreTarea -Action $accion -Trigger $disparador -Settings $ajustes `
        -Description 'Informe de estado de Whetzy (solo lectura). docs/ESTADO_AUTOMATICO.md' -Force | Out-Null
    Write-Host "Tarea «$NombreTarea» registrada: cada $CadaHoras h, empieza en 1 minuto."
    return
}

$base = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { Join-Path $HOME '.cache' }
$Cache = Join-Path $base 'whetzy-cache/estado'
$Historial = Join-Path $Cache 'historial'
New-Item -ItemType Directory -Force -Path $Historial | Out-Null

$python = $null
foreach ($candidato in @('python', 'python3', 'py')) {
    if (Get-Command $candidato -ErrorAction SilentlyContinue) { $python = $candidato; break }
}
if (-not $python) { throw 'No encuentro Python (python, python3 o py) en el PATH.' }

if (-not $env:GITHUB_TOKEN -and (Get-Command gh -ErrorAction SilentlyContinue)) {
    $token = (& gh auth token 2>$null)
    if ($LASTEXITCODE -eq 0 -and $token) { $env:GITHUB_TOKEN = $token.Trim() }
}

$sello = Get-Date -Format 'yyyyMMdd-HHmmss'
$md = Join-Path $Cache 'informe.md'
$previo = Join-Path $Cache 'estado.json'
$nuevo = Join-Path $Cache "estado-$sello.json"

$argumentos = @('scripts/estado.py', '--out', $md, '--json', $nuevo, '--state', $previo, '--repo-dir', $Raiz)
if ($SinRepo) { $argumentos += '--sin-repo' }
if ($python -eq 'py') { $argumentos = @('-3') + $argumentos }

Push-Location $Raiz
try {
    & $python @argumentos | Out-Null
    $salida = $LASTEXITCODE
} finally {
    Pop-Location
}

if (Test-Path $nuevo) {
    Copy-Item $md (Join-Path $Historial "informe-$sello.md")
    Move-Item -Force $nuevo $previo
}
Get-ChildItem $Historial -Filter 'informe-*.md' | Sort-Object Name -Descending | Select-Object -Skip 60 |
    Remove-Item -Force

$alertas = @(Select-String -Path $md -Pattern '^\| 🛑 ' -ErrorAction SilentlyContinue)
Write-Host ("Informe: $md · alertas: {0} · código de salida: {1}" -f $alertas.Count, $salida)
foreach ($a in $alertas) { Write-Host ("  " + $a.Line) -ForegroundColor Red }
if ($Abrir) { Invoke-Item $md }
exit $salida
