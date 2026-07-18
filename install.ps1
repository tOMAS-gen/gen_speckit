#Requires -Version 5.1
<#
.SYNOPSIS
  Instala gen_speckit (spec-kit oficial + mejoras multi-CLI) en un proyecto.
.DESCRIPTION
  Reproduce el gesto del spec-kit original y le suma SOLO el producto de este repo:
    1. Si el proyecto no tiene .specify/, corre el `specify init` oficial de GitHub
       (requiere specify-cli instalado: uv tool install specify-cli --from
       git+https://github.com/github/spec-kit.git).
    2. Copia las mejoras multi-CLI segun un manifiesto explicito: 8 skills nuevas,
       playbooks portables, 6 scripts PowerShell, catalogo de CLIs y punteros de
       portabilidad. NADA del desarrollo de gen_speckit (specs, constitucion,
       agentes, tests, README) se copia al proyecto destino.
.EXAMPLE
  # En la carpeta del proyecto destino:
  irm https://raw.githubusercontent.com/tOMAS-gen/gen_speckit/main/install.ps1 | iex
.EXAMPLE
  # Desde un clon local del repo:
  E:\gen_speckit\install.ps1 -Destino C:\mi-proyecto
#>
[CmdletBinding()]
param(
    [string]$Destino = (Get-Location).Path,
    [string]$Integracion = 'claude',
    [string]$Script = 'ps',
    [switch]$SinInit,     # saltear el specify init oficial (ya inicializado a mano)
    [string]$Fuente = ''  # clon local del repo; vacio = descargar de GitHub
)

$ErrorActionPreference = 'Stop'
$repoZip = 'https://github.com/tOMAS-gen/gen_speckit/archive/refs/heads/main.zip'

# ---------------------------------------------------------------- manifiesto ---
$SkillsNuevas = @(
    'speckit-models', 'speckit-clis', 'speckit-agents', 'speckit-readme',
    'speckit-orchestrate', 'speckit-constitution-plus',
    'speckit-specify-auto', 'speckit-specify-auto-eco'
)
$ScriptsNuevos = @(
    'platform.ps1', 'scan-models.ps1', 'invoke-secondary.ps1',
    'update-quota.ps1', 'get-parallel-groups.ps1', 'clis-config.ps1'
)

Write-Host '=== gen_speckit: instalador (spec-kit oficial + mejoras multi-CLI) ===' -ForegroundColor Cyan
Write-Host "Destino: $Destino"

# ------------------------------------------------- 1) specify init oficial ---
$specifyDir = Join-Path $Destino '.specify'
if (-not $SinInit -and -not (Test-Path $specifyDir)) {
    $specify = Get-Command specify -ErrorAction SilentlyContinue
    if ($null -eq $specify) {
        Write-Host ''
        Write-Host 'Falta el spec-kit oficial. Instalalo primero (una sola vez):' -ForegroundColor Yellow
        Write-Host '  uv tool install specify-cli --from git+https://github.com/github/spec-kit.git'
        Write-Host 'y volve a correr este instalador.'
        exit 1
    }
    Write-Host "Paso 1/2: specify init . --integration $Integracion --script $Script"
    Push-Location $Destino
    try { & specify init . --integration $Integracion --script $Script } finally { Pop-Location }
    if (-not (Test-Path $specifyDir)) { throw 'specify init no creo .specify/ — revisar la salida anterior.' }
} else {
    Write-Host 'Paso 1/2: .specify/ ya existe (o -SinInit) — se conserva la base actual.'
}

# --------------------------------------------------- 2) obtener la fuente ---
$cleanupTemp = $null
if ($Fuente -and (Test-Path (Join-Path $Fuente '.specify\orchestrator'))) {
    $src = $Fuente
} elseif (Test-Path (Join-Path $PSScriptRoot '.specify\orchestrator')) {
    $src = $PSScriptRoot
} else {
    Write-Host 'Descargando gen_speckit desde GitHub...'
    $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("gen_speckit_" + [guid]::NewGuid().ToString('N').Substring(0, 8))
    $null = New-Item -ItemType Directory -Force -Path $tmp
    $zip = Join-Path $tmp 'repo.zip'
    Invoke-WebRequest -Uri $repoZip -OutFile $zip -UseBasicParsing
    Expand-Archive -Path $zip -DestinationPath $tmp -Force
    $src = (Get-ChildItem $tmp -Directory | Where-Object { $_.Name -like 'gen_speckit*' } | Select-Object -First 1).FullName
    $cleanupTemp = $tmp
}
Write-Host "Fuente: $src"

# ------------------------------------------------ 3) copiar el manifiesto ---
Write-Host 'Paso 2/2: copiando las mejoras multi-CLI...'
$copiados = New-Object System.Collections.ArrayList

function Copy-Item2 {
    param([string]$Rel, [string]$DestRel = '')
    # [string]$null se convierte en '' — comparar por vacio, no por null (quirk PS).
    if ([string]::IsNullOrEmpty($DestRel)) { $DestRel = $Rel }
    $from = Join-Path $src $Rel
    $to = Join-Path $Destino $DestRel
    if (-not (Test-Path $from)) { Write-Warning "no encontrado en la fuente: $Rel"; return }
    $toDir = Split-Path -Parent $to
    if ($toDir -and -not (Test-Path $toDir)) { $null = New-Item -ItemType Directory -Force -Path $toDir }
    Copy-Item -Path $from -Destination $to -Recurse -Force
    [void]$copiados.Add($DestRel)
}

foreach ($s in $SkillsNuevas) { Copy-Item2 (Join-Path '.claude\skills' $s) }
Copy-Item2 '.specify\orchestrator'
foreach ($f in $ScriptsNuevos) { Copy-Item2 (Join-Path '.specify\scripts\powershell' $f) }
Copy-Item2 '.specify\clis-catalog.json'
Copy-Item2 '.codex\prompts\speckit-orchestrate.md'

# AGENTS.md: nunca pisar el del proyecto destino.
$agentsDest = Join-Path $Destino 'AGENTS.md'
if (Test-Path $agentsDest) {
    Copy-Item2 'AGENTS.md' 'AGENTS.gen-speckit.md'
    Write-Warning 'AGENTS.md ya existia: las instrucciones multi-CLI quedaron en AGENTS.gen-speckit.md (integralas a mano si queres).'
} else {
    Copy-Item2 'AGENTS.md'
}

# .gitignore del destino: datos locales del sistema multi-CLI.
$gi = Join-Path $Destino '.gitignore'
$giLineas = @('.specify/models.json', '.specify/models.scan.json', 'specs/**/orchestration-logs/')
$giActual = if (Test-Path $gi) { Get-Content $gi -Raw -Encoding UTF8 } else { '' }
$agregar = @($giLineas | Where-Object { $giActual -notmatch [regex]::Escape($_) })
if ($agregar.Count -gt 0) {
    $bloque = "`n# gen_speckit: datos locales del sistema multi-CLI`n" + ($agregar -join "`n") + "`n"
    [System.IO.File]::AppendAllText($gi, $bloque, (New-Object System.Text.UTF8Encoding($false)))
    [void]$copiados.Add('.gitignore (+3 exclusiones)')
}

if ($cleanupTemp) { Remove-Item $cleanupTemp -Recurse -Force -ErrorAction SilentlyContinue }

# -------------------------------------------------------------- resumen ---
Write-Host ''
Write-Host "Instalado ($($copiados.Count) elementos):" -ForegroundColor Green
$copiados | ForEach-Object { Write-Host "  + $_" }
Write-Host ''
Write-Host 'Proximos pasos:' -ForegroundColor Cyan
Write-Host '  1. /speckit-models          -> genera el inventario de CLIs de esta maquina'
Write-Host '  2. /speckit-constitution-plus "<principios>"  -> constitucion + agentes del proyecto'
Write-Host '  3. /speckit-specify-auto "<tu idea>"          -> el circuito completo'
