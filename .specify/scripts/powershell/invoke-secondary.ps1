#Requires -Version 5.1
<#
.SYNOPSIS
  Invoca un CLI secundario en modo headless para ejecutar una tarea, con timeout,
  1 reintento ante fallo transitorio y clasificacion del resultado
  (exito | cuota_agotada | indisponible).
.DESCRIPTION
  GENERICO (feature 003): sin nombres de CLI en el codigo. El comando sale de la
  plantilla headless del inventario; los patrones de cuota y hints de ejecutable se
  resuelven inventario > catalogo > defaults genericos. La ejecucion es portable
  (Windows/Linux/macOS) via platform.ps1.
.NOTES
  Dot-source para importar funciones sin ejecutar (tests).
#>
[CmdletBinding()]
param(
    [string]$Cli,
    [string]$Model,
    [string]$Prompt,
    [string]$ModelsPath,
    [string]$LogDir,
    [string]$LogBaseName = 'tarea',
    [int]$TimeoutSeconds = 900,   # 15 min por defecto (FR-016)
    [string]$WorkingDirectory = (Get-Location).Path
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

# Reusa helpers genericos (catalogo, JSON canonico) y de plataforma (transitivo).
. (Join-Path (Split-Path -Parent $PSCommandPath) 'scan-models.ps1')

function Get-CliDataValue {
    # Resolucion generica inventario > catalogo para un campo de un CLI, tolerante a
    # PSCustomObject o hashtable en cualquiera de las dos fuentes.
    param($Inventory, $Catalog, [string]$Cli, [string]$Key, $Default = $null)
    foreach ($source in @($Inventory, $Catalog)) {
        if ($null -eq $source) { continue }
        $plain = ConvertTo-PlainValue $source
        if ($plain.Contains('clis') -and $plain['clis'].Contains($Cli)) {
            $entry = $plain['clis'][$Cli]
            if ($entry -is [System.Collections.IDictionary] -and $entry.Contains($Key) -and $null -ne $entry[$Key]) {
                return $entry[$Key]
            }
        }
    }
    $Default
}

function Get-QuotaPatternsFor {
    # Patrones de cuota agotada: inventario > catalogo del CLI > genericos del
    # catalogo > respaldo interno (FR-012).
    param($Inventory, $Catalog, [string]$Cli)
    $patterns = Get-CliDataValue $Inventory $Catalog $Cli 'patrones_cuota' $null
    if ($null -ne $patterns -and @($patterns).Count -gt 0) { return ,@($patterns) }
    if ($null -ne $Catalog) {
        $plain = ConvertTo-PlainValue $Catalog
        if ($plain.Contains('patrones_cuota_genericos') -and @($plain['patrones_cuota_genericos']).Count -gt 0) {
            return ,@($plain['patrones_cuota_genericos'])
        }
    }
    ,@(Get-DefaultQuotaPatterns)
}

function Get-HeadlessCommand {
    # Construye el comando concreto desde la plantilla del inventario.
    param($Inventory, [string]$Cli, [string]$Model, [string]$Prompt)
    $plain = ConvertTo-PlainValue $Inventory
    if (-not ($plain.Contains('clis') -and $plain['clis'].Contains($Cli))) {
        throw "CLI '$Cli' no existe en el inventario"
    }
    $entry = $plain['clis'][$Cli]
    $template = if ($entry.Contains('headless')) { [string]$entry['headless'] } else { '' }
    if ([string]::IsNullOrWhiteSpace($template)) { throw "CLI '$Cli' no tiene plantilla headless" }
    # Colapsar saltos de linea y espacios multiples: el wrapper ejecuta UNA linea de
    # comando — un prompt con newline final la partiria en dos (bug real detectado:
    # la segunda mitad se ejecutaba como comando basura y ensuciaba el exit code).
    $sanitized = (($Prompt -replace '\s+', ' ').Trim())
    $escapedPrompt = $sanitized -replace '"', '\"'
    $command = $template -replace '\{prompt\}', $escapedPrompt
    if ($command -match '\{modelo\}') {
        $command = $command -replace '\{modelo\}', $Model
    } elseif ($Model) {
        $command = "$command --model $Model"
    }
    $command
}

function Test-QuotaPattern {
    # $true si el texto matchea algun patron de limite de uso.
    param([string[]]$Patterns, [string]$Text)
    if ([string]::IsNullOrEmpty($Text)) { return $false }
    foreach ($p in $Patterns) {
        if ($Text -imatch $p) { return $true }
    }
    $false
}

function Invoke-SecondaryTask {
    <#
      Ciclo completo (Clarificacion S4 + FR-018):
        intento 1 -> exito | cuota_agotada (sin reintento) | fallo transitorio
        fallo transitorio -> intento 2 -> exito | cuota_agotada | indisponible
    #>
    param(
        [string]$Cli, [string]$Model, [string]$Prompt,
        $Inventory,
        $Catalog = $null,
        [string]$LogDir, [string]$LogBaseName = 'tarea',
        [int]$TimeoutSeconds = 900,
        [string]$WorkingDirectory = (Get-Location).Path
    )
    if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Force -Path $LogDir | Out-Null }
    $command = Get-HeadlessCommand -Inventory $Inventory -Cli $Cli -Model $Model -Prompt $Prompt

    # Resolver el ejecutable a ruta completa (el PATH de los hijos no es confiable);
    # hints adicionales (p. ej. binarios dentro de paquetes) vienen de los datos.
    $exeHints = @(Get-CliDataValue $Inventory $Catalog $Cli 'exe_hints' @())
    $exe = Resolve-Executable -Name $Cli -ExeHints $exeHints
    if ($null -ne $exe) {
        $command = $command -replace "^\s*$([regex]::Escape($Cli))(?=\s)", "`"$exe`""
    }

    $patterns = Get-QuotaPatternsFor $Inventory $Catalog $Cli
    $intentos = 0
    $clasificacion = $null
    $lastExit = $null
    $outFile = $null; $errFile = $null

    while ($intentos -lt 2) {
        $intentos++
        $outFile = Join-Path $LogDir "$LogBaseName.intento$intentos.out.log"
        $errFile = Join-Path $LogDir "$LogBaseName.intento$intentos.err.log"
        $r = Invoke-PortableProcess -Command $command -TimeoutSeconds $TimeoutSeconds `
            -OutFile $outFile -ErrFile $errFile -WorkDir $WorkingDirectory
        $lastExit = $r.exitCode
        $texto = ''
        if (Test-Path $outFile) { $texto += (Get-Content $outFile -Raw) }
        if (Test-Path $errFile) { $texto += "`n" + (Get-Content $errFile -Raw) }

        if (-not $r.timedOut -and $r.exitCode -eq 0) { $clasificacion = 'exito'; break }
        if (Test-QuotaPattern -Patterns $patterns -Text $texto) { $clasificacion = 'cuota_agotada'; break }
        # Fallo transitorio (timeout incluido): 1 reintento; al segundo, indisponible.
        if ($intentos -ge 2) { $clasificacion = 'indisponible' }
    }

    [pscustomobject]@{
        clasificacion = $clasificacion
        intentos      = $intentos
        exitCode      = $lastExit
        stdoutPath    = $outFile
        stderrPath    = $errFile
        comando       = $command
    }
}

if ($MyInvocation.InvocationName -ne '.') {
    foreach ($req in @('Cli', 'Prompt', 'ModelsPath', 'LogDir')) {
        if (-not (Get-Variable $req -ValueOnly)) { throw "Falta -$req" }
    }
    $inventory = Get-Content $ModelsPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $repoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSCommandPath)))
    $catalog = Get-CliCatalog -RepoRoot $repoRoot 3>$null
    $result = Invoke-SecondaryTask -Cli $Cli -Model $Model -Prompt $Prompt -Inventory $inventory `
        -Catalog $catalog -LogDir $LogDir -LogBaseName $LogBaseName -TimeoutSeconds $TimeoutSeconds `
        -WorkingDirectory $WorkingDirectory
    ConvertTo-Json -InputObject $result -Depth 4
    if ($result.clasificacion -ne 'exito') { exit 1 } else { exit 0 }
}
