#Requires -Version 5.1
<#
.SYNOPSIS
  Detecta CLIs de IA y genera .specify/models.json con inventario y ranking.
.DESCRIPTION
  GENERICO (feature 003): ningun nombre de CLI vive en este codigo. Los CLIs
  conocidos y sus datos (plantillas, semillas, hints) salen del catalogo versionado
  .specify/clis-catalog.json; los CLIs registrados por el usuario salen del propio
  inventario. Resolucion de datos: inventario > catalogo > defaults genericos.
  - Preserva ediciones manuales comparando contra .specify/models.scan.json.
  - Respeta la marca `deshabilitado` (excluye del ranking sin borrar).
  - Salida UTF-8 sin BOM, indentacion 2.
.NOTES
  Dot-source para importar funciones sin ejecutar (tests).
#>
[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$Force,
    [switch]$ProbeAuth,
    [string]$RepoRoot
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

. (Join-Path (Split-Path -Parent $PSCommandPath) 'platform.ps1')

function Get-DefaultQuotaPatterns {
    # Respaldo final si ni inventario ni catalogo declaran patrones (FR-012).
    @('rate limit', 'quota', '\b429\b', 'usage limit')
}

function Get-CliCatalog {
    # Catalogo versionado. Ausente o corrupto NO es fatal: se avisa y se sigue con
    # el inventario + defaults (contracts/clis-catalog inv. 4).
    param([string]$RepoRoot)
    $path = Join-Path $RepoRoot (Join-Path '.specify' 'clis-catalog.json')
    if (-not (Test-Path $path)) {
        Write-Warning "Catalogo de CLIs no encontrado ($path); se continua con el inventario y defaults genericos."
        return [ordered]@{ version = 0; patrones_cuota_genericos = @(Get-DefaultQuotaPatterns); clis = [ordered]@{} }
    }
    try {
        ConvertTo-PlainValue (Get-Content $path -Raw -Encoding UTF8 | ConvertFrom-Json)
    } catch {
        Write-Warning "Catalogo de CLIs invalido ($($_.Exception.Message)); se continua con el inventario y defaults genericos."
        [ordered]@{ version = 0; patrones_cuota_genericos = @(Get-DefaultQuotaPatterns); clis = [ordered]@{} }
    }
}

function Get-CatalogCliValue {
    # Resolucion inventario > catalogo > default para un campo de un CLI.
    param($Existing, $Catalog, [string]$Cli, [string]$Key, $Default = $null)
    if ($null -ne $Existing -and $Existing.Contains('clis') -and $Existing['clis'].Contains($Cli)) {
        $entry = $Existing['clis'][$Cli]
        if ($entry -is [System.Collections.IDictionary] -and $entry.Contains($Key)) { return $entry[$Key] }
    }
    if ($null -ne $Catalog -and $Catalog.Contains('clis') -and $Catalog['clis'].Contains($Cli)) {
        $entry = $Catalog['clis'][$Cli]
        if ($entry -is [System.Collections.IDictionary] -and $entry.Contains($Key)) { return $entry[$Key] }
    }
    $Default
}

function Get-CliNames {
    # Union ordenada: primero los del catalogo, despues los registrados del inventario.
    param($Catalog, $Existing)
    $names = New-Object System.Collections.ArrayList
    if ($null -ne $Catalog -and $Catalog.Contains('clis')) {
        foreach ($n in $Catalog['clis'].Keys) { [void]$names.Add($n) }
    }
    if ($null -ne $Existing -and $Existing.Contains('clis')) {
        foreach ($n in $Existing['clis'].Keys) { if (-not $names.Contains($n)) { [void]$names.Add($n) } }
    }
    ,@($names.ToArray())
}

function Get-CliDetection {
    # Sondeo local generico: instalado (resolucion portable) y version (version_cmd).
    param([string]$Name, [string]$VersionCmd = '--version', [string[]]$ExeHints = @())
    $result = [ordered]@{ instalado = $false; version = 'desconocido' }
    $exe = Resolve-Executable -Name $Name -ExeHints $ExeHints
    if ($null -ne $exe) {
        $result.instalado = $true
        try {
            $args = @($VersionCmd -split '\s+')
            $v = (& $exe @args 2>&1 | Select-Object -First 1 | Out-String).Trim()
            if ($v) { $result.version = $v }
        } catch { }
    }
    $result
}

function Get-AuthStatus {
    # Best-effort por hints de credenciales del SO actual; -Probe hace una invocacion
    # minima real (consume una llamada).
    param([string]$Name, [string[]]$AuthHints = @(), [string]$Headless = '', [switch]$Probe)
    foreach ($hint in $AuthHints) {
        $expanded = Expand-PortablePath $hint
        if (Test-Path $expanded) { return $true }
    }
    if ($Probe -and $Headless) {
        try {
            $cmd = $Headless -replace '\s*--model\s+\S*\{modelo\}\S*', '' -replace '\{prompt\}', 'responde solo: ok'
            $null = cmd /c "$cmd 2>&1"
            if ($LASTEXITCODE -eq 0) { return $true } else { return $false }
        } catch { return $false }
    }
    'desconocido'
}

function Get-AuthHintsForOs {
    param($AuthHints)
    if ($null -eq $AuthHints) { return @() }
    $os = Get-OsFamily
    if ($AuthHints -is [System.Collections.IDictionary] -and $AuthHints.Contains($os)) {
        return @($AuthHints[$os])
    }
    @()
}

function Build-Inventory {
    # Construye la seccion clis. Datos por CLI: inventario existente > catalogo.
    param(
        [hashtable]$Detections,   # nombre -> @{instalado; version}
        [hashtable]$AuthStatus,   # nombre -> $true|$false|'desconocido'
        $Catalog = $null,
        $Existing = $null
    )
    $clis = [ordered]@{}
    foreach ($cli in $Detections.Keys | Sort-Object) {
        $det = $Detections[$cli]
        $headless = Get-CatalogCliValue $Existing $Catalog $cli 'headless' ''
        $modelos = Get-CatalogCliValue $Existing $Catalog $cli 'modelos' $null
        if ($null -eq $modelos) {
            $modelos = Get-CatalogCliValue $null $Catalog $cli 'modelos_semilla' @()
        }
        $origen = 'registrado'
        if ($null -ne $Catalog -and $Catalog.Contains('clis') -and $Catalog['clis'].Contains($cli)) { $origen = 'catalogo' }
        $entry = [ordered]@{
            instalado   = [bool]$det.instalado
            autenticado = $AuthStatus[$cli]
            version     = $det.version
            headless    = $headless
            origen      = $origen
            plan        = (Get-CatalogCliValue $Existing $null $cli 'plan' 'desconocido')
            cuota       = (Get-CatalogCliValue $Existing $null $cli 'cuota' 'desconocido')
            modelos     = @($modelos)
        }
        $deshabilitado = Get-CatalogCliValue $Existing $null $cli 'deshabilitado' $false
        if ($deshabilitado) { $entry['deshabilitado'] = $true }
        $patrones = Get-CatalogCliValue $Existing $Catalog $cli 'patrones_cuota' $null
        if ($null -ne $patrones) { $entry['patrones_cuota'] = @($patrones) }
        $clis[$cli] = $entry
    }
    $clis
}

function Build-Asignacion {
    # Listas ordenadas por nivel. Nunca excluye un CLI instalado y habilitado
    # (Constitucion IV). Nivel vacio -> mejores disponibles.
    param($Clis)
    $available = @()
    foreach ($cli in $Clis.Keys) {
        $entry = $Clis[$cli]
        if (-not $entry.instalado) { continue }
        if ($entry.Contains('deshabilitado') -and $entry['deshabilitado']) { continue }
        foreach ($m in $entry.modelos) {
            $available += [pscustomobject]@{
                ref = "$cli/$($m.id)"; capacidad = $m.capacidad; costo = $m.costo
            }
        }
    }
    $levels = [ordered]@{
        alta  = @($available | Where-Object { $_.capacidad -ge 8 } | Sort-Object @{e='capacidad';Descending=$true}, costo)
        media = @($available | Where-Object { $_.capacidad -ge 6 } | Sort-Object costo, @{e='capacidad';Descending=$true})
        baja  = @($available | Sort-Object costo, capacidad)
    }
    $asignacion = [ordered]@{}
    foreach ($name in @('alta','media','baja')) {
        $list = $levels[$name]
        if ($list.Count -eq 0) {
            $list = @($available | Sort-Object @{e='capacidad';Descending=$true}, costo)
        }
        $asignacion[$name] = @($list | ForEach-Object { $_.ref })
    }
    $asignacion
}

function ConvertTo-PlainValue {
    # Normaliza PSCustomObject/hashtable a estructuras comparables.
    param($Value)
    if ($Value -is [System.Management.Automation.PSCustomObject]) {
        $h = [ordered]@{}
        foreach ($p in $Value.PSObject.Properties) { $h[$p.Name] = ConvertTo-PlainValue $p.Value }
        return $h
    }
    if ($Value -is [System.Collections.IDictionary]) {
        $h = [ordered]@{}
        foreach ($k in $Value.Keys) { $h[$k] = ConvertTo-PlainValue $Value[$k] }
        return $h
    }
    if (($Value -is [array]) -or ($Value -is [System.Collections.IList] -and $Value -isnot [string])) {
        # La coma evita que PS desenrolle arrays de un elemento en la frontera de la funcion.
        return ,@($Value | ForEach-Object { ConvertTo-PlainValue $_ })
    }
    $Value
}

function Merge-PreservingUserEdits {
    <#
      Regla (FR-004): un valor del models.json existente que difiere de la propuesta
      previa (models.scan.json) fue editado por el usuario y PREVALECE. Sin propuesta
      previa, todo el existente es del usuario. Con -Force gana la propuesta nueva.
    #>
    param($Proposed, $Existing, $PrevScan, [switch]$Force)
    if ($Force -or $null -eq $Existing) { return $Proposed }
    $prop = ConvertTo-PlainValue $Proposed
    $exis = ConvertTo-PlainValue $Existing
    $prev = if ($null -ne $PrevScan) { ConvertTo-PlainValue $PrevScan } else { $null }
    Merge-Node $prop $exis $prev
}

function Merge-Node {
    param($Prop, $Exis, $Prev)
    if ($Exis -is [System.Collections.IDictionary] -and $Prop -is [System.Collections.IDictionary]) {
        $out = [ordered]@{}
        $keys = @($Prop.Keys) + @($Exis.Keys | Where-Object { -not $Prop.Contains($_) })
        foreach ($k in $keys) {
            # Asignacion directa (no via expresion if) para no enumerar arrays de 1 elemento.
            $prevChild = $null
            if ($Prev -is [System.Collections.IDictionary] -and $Prev.Contains($k)) { $prevChild = $Prev[$k] }
            if (-not $Prop.Contains($k)) { $out[$k] = $Exis[$k]; continue }   # campo agregado por el usuario
            if (-not $Exis.Contains($k)) { $out[$k] = $Prop[$k]; continue }   # campo nuevo del scan
            $out[$k] = Merge-Node $Prop[$k] $Exis[$k] $prevChild
        }
        return $out
    }
    # Hojas y arrays: si el existente difiere de la propuesta previa -> edicion manual, prevalece.
    $exisJson = ConvertTo-Json -InputObject $Exis -Depth 10 -Compress
    $prevJson = if ($null -ne $Prev) { ConvertTo-Json -InputObject $Prev -Depth 10 -Compress } else { $null }
    if ($null -eq $prevJson -or $exisJson -ne $prevJson) { $winner = $Exis } else { $winner = $Prop }
    if ($winner -is [System.Collections.IList] -and $winner -isnot [string]) { return ,$winner }
    return $winner
}

function ConvertTo-JsonStringLiteral {
    param([string]$s)
    $escaped = $s -replace '\\', '\\' -replace '"', '\"' -replace "`r", '\r' -replace "`n", '\n' -replace "`t", '\t'
    '"' + $escaped + '"'
}

function ConvertTo-CanonicalJson {
    # Serializador propio: JSON deterministico con indentacion 2 (el ConvertTo-Json
    # nativo usa un formato irregular que rompe el invariante del contrato).
    param($Value, [int]$Indent = 0)
    $pad = ' ' * $Indent
    $childIndent = $Indent + 2
    $childPad = ' ' * $childIndent
    if ($null -eq $Value) { return 'null' }
    if ($Value -is [bool]) { if ($Value) { return 'true' } else { return 'false' } }
    if ($Value -is [int] -or $Value -is [long] -or $Value -is [double] -or $Value -is [decimal]) { return "$Value" }
    if ($Value -is [System.Management.Automation.PSCustomObject]) {
        $Value = ConvertTo-PlainValue $Value
    }
    if ($Value -is [System.Collections.IDictionary]) {
        if ($Value.Keys.Count -eq 0) { return '{}' }
        $parts = foreach ($k in $Value.Keys) {
            "$childPad$(ConvertTo-JsonStringLiteral ([string]$k)): $(ConvertTo-CanonicalJson $Value[$k] $childIndent)"
        }
        return "{`n" + ($parts -join ",`n") + "`n$pad}"
    }
    if ($Value -is [System.Collections.IList] -and $Value -isnot [string]) {
        if ($Value.Count -eq 0) { return '[]' }
        $parts = foreach ($v in $Value) { "$childPad$(ConvertTo-CanonicalJson $v $childIndent)" }
        return "[`n" + ($parts -join ",`n") + "`n$pad]"
    }
    ConvertTo-JsonStringLiteral ([string]$Value)
}

function ConvertTo-Json2Space {
    param($Object)
    (ConvertTo-CanonicalJson $Object 0) + "`n"
}

function Invoke-ScanModels {
    param(
        [string]$RepoRoot,
        [switch]$Force,
        [switch]$ProbeAuth,
        [switch]$Json
    )
    if (-not $RepoRoot) {
        # Este script vive en <root>\.specify\scripts\powershell\ -> subir 3 niveles.
        $scriptDir = Split-Path -Parent $PSCommandPath
        $RepoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $scriptDir))
    }
    $modelsPath = Join-Path $RepoRoot (Join-Path '.specify' 'models.json')
    $scanPath   = Join-Path $RepoRoot (Join-Path '.specify' 'models.scan.json')

    $catalog = Get-CliCatalog -RepoRoot $RepoRoot
    $existing = $null
    $prevScan = $null
    if (Test-Path $modelsPath) {
        try { $existing = ConvertTo-PlainValue (Get-Content $modelsPath -Raw -Encoding UTF8 | ConvertFrom-Json) } catch {
            Write-Warning "models.json existente es invalido ($($_.Exception.Message)); se regenera desde cero."
        }
    }
    if (Test-Path $scanPath) {
        try { $prevScan = Get-Content $scanPath -Raw -Encoding UTF8 | ConvertFrom-Json } catch { }
    }

    $names = Get-CliNames -Catalog $catalog -Existing $existing
    $detections = @{}
    $auth = @{}
    foreach ($cli in $names) {
        $versionCmd = Get-CatalogCliValue $existing $catalog $cli 'version_cmd' '--version'
        $exeHints = @(Get-CatalogCliValue $existing $catalog $cli 'exe_hints' @())
        $detections[$cli] = Get-CliDetection -Name $cli -VersionCmd $versionCmd -ExeHints $exeHints
        if ($detections[$cli].instalado) {
            $hints = Get-AuthHintsForOs (Get-CatalogCliValue $existing $catalog $cli 'auth_hints' $null)
            $headless = Get-CatalogCliValue $existing $catalog $cli 'headless' ''
            $auth[$cli] = Get-AuthStatus -Name $cli -AuthHints $hints -Headless $headless -Probe:$ProbeAuth
        } else {
            $auth[$cli] = $false
        }
    }

    $clis = Build-Inventory -Detections $detections -AuthStatus $auth -Catalog $catalog -Existing $existing
    $proposed = [ordered]@{
        clis       = $clis
        asignacion = Build-Asignacion $clis
    }

    $final = Merge-PreservingUserEdits -Proposed $proposed -Existing $existing -PrevScan $prevScan -Force:$Force

    Write-Utf8NoBom -Path $scanPath   -Content (ConvertTo-Json2Space $proposed)
    Write-Utf8NoBom -Path $modelsPath -Content (ConvertTo-Json2Space $final)

    if ($Json) {
        $summary = [ordered]@{
            MODELS_JSON = $modelsPath
            SCAN_JSON   = $scanPath
            CLIS        = [ordered]@{}
        }
        foreach ($cli in $names) {
            $summary.CLIS[$cli] = [ordered]@{
                instalado = $detections[$cli].instalado
                version   = $detections[$cli].version
                autenticado = $auth[$cli]
            }
        }
        $summary | ConvertTo-Json -Depth 5 -Compress
    } else {
        Write-Host "Inventario escrito en $modelsPath"
        foreach ($cli in $names) {
            $st = if ($detections[$cli].instalado) { "instalado ($($detections[$cli].version))" } else { 'AUSENTE' }
            Write-Host ("  {0,-12} {1}" -f $cli, $st)
        }
        Write-Host "Revisa y corrige a mano: plan, cuota, capacidad/costo. Tus ediciones prevalecen."
    }
}

if ($MyInvocation.InvocationName -ne '.') {
    Invoke-ScanModels -RepoRoot $RepoRoot -Force:$Force -ProbeAuth:$ProbeAuth -Json:$Json
    # Los version_cmd de CLIs externos pueden dejar LASTEXITCODE sucio; el scan fue exitoso.
    exit 0
}
