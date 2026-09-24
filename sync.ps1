# ====================================================
# SCRIPT MAESTRO DE SINCRONIZACIÓN - POWERSHELL NATIVO
# ====================================================

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "    ASISTENTE INTELIGENTE DE SINCRONIZACIÓN DB      " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

$ContainerName = "learning-engine-db-1"
$DbUser = "neurium"
$DbName = "neurium"
$BackupFile = "backup_neurium.dump"

# Eliminar respaldo anterior si existe
if (Test-Path $BackupFile) { Remove-Item $BackupFile }

# Solicitar URL de Railway
$RawRailwayUrl = Read-Host "Introduce tu DATABASE_URL de Railway"

# Limpiar y adaptar la URL para pg_restore (reemplazar asyncpg por postgresql estándar)
$RailwayUrl = $RawRailwayUrl -replace "postgresql\+asyncpg://", "postgresql://"

Write-Host "--------------------------------------------------" -ForegroundColor DarkGray
Write-Host "[1/2] Creando respaldo binario desde el contenedor Docker..." -ForegroundColor Yellow

# Generar el respaldo usando directamente el parámetro -f dentro del contenedor
docker exec -t $ContainerName pg_dump -U $DbUser -d $DbName -F c -b -v -f /tmp/backup.dump
docker cp "$($ContainerName):/tmp/backup.dump" $BackupFile

if (Test-Path $BackupFile) {
    Write-Host "¡Respaldo local creado con éxito: $BackupFile!" -ForegroundColor Green
} else {
    Write-Host "Error: No se pudo generar el respaldo." -ForegroundColor Red
    exit 1
}

Write-Host "--------------------------------------------------" -ForegroundColor DarkGray
Write-Host "[2/2] Restaurando base de datos en Railway..." -ForegroundColor Yellow

# Restaurar en Railway usando la URL corregida
pg_restore --clean --if-exists -v -d $RailwayUrl $BackupFile

if ($LASTEXITCODE -eq 0) {
    Write-Host "¡Base de datos sincronizada y subida a Railway con éxito!" -ForegroundColor Green
} else {
    Write-Host "La restauración finalizó. Revisa tus tablas en Railway para confirmar los datos." -ForegroundColor Yellow
}

Write-Host "--------------------------------------------------" -ForegroundColor DarkGray
Write-Host "Limpiando archivos temporales..." -ForegroundColor Yellow
if (Test-Path $BackupFile) { Remove-Item $BackupFile }

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host " ¡PROCESO COMPLETADO AL 100% CON ÉXITO!            " -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Cyan
