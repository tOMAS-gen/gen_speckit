#Requires -Version 5.1
<#
.SYNOPSIS
  Detecta CLIs de IA instalados (claude/codex/kimi) y genera .specify/models.json
  con el inventario y ranking de modelos por complejidad.
.DESCRIPTION
  - Deteccion automatica: instalado, version, plantilla headless, autenticacion
    (best-effort por archivos de credenciales; -ProbeAuth hace una invocacion real).
  - Siembra capacidad/costo/contexto desde una tabla estatica corregible.
  - Preserva ediciones manuales del usuario: compara models.json existente contra la
    propuesta previa (.specify/models.scan.json); lo que difiere es del usuario y
    prevalece salvo -Force.
  - Salida UTF-8 sin BOM, indentacion 2 espacios (contrato models-schema).
.NOTES
  Dot-source (`. .\scan-models.ps1`) para importar las funciones sin ejecutar (tests).
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

$script:CliNames = @('claude', 'codex', 'kimi')

function Get-DefaultHeadless {
    param([string]$Cli)
    switch ($Cli) {
        'claude' { 'claude -p "{prompt}" --dangerously-skip-permissions --output-format json' }
        # codex 0.144+: exec es no-interactivo por defecto (--ask-for-approval ya no existe).
        # danger-full-access implementa la Clarificacion S2 (permisos totales dentro del
        # repo, verificacion del principal como control); workspace-write monta solo
        # lectura cuando el proyecto no es un repo git.
        'codex'  { 'codex exec "{prompt}" --sandbox danger-full-access --skip-git-repo-check --json' }
        # Kimi Code usa alias calificados (config.toml: default_model = "kimi-code/k3").
        # kimi-code 0.27+: -p ya es no-interactivo y NO se combina con --yolo.
        'kimi'   { 'kimi -p "{prompt}" --model kimi-code/{modelo} --output-format text' }
    }
}

function Get-SeedModels {
    # Tabla estatica de siembra (research R6), actualizada 2026-07 con los pickers
    # reales de cada CLI. El usuario corrige a mano en models.json; el id es el alias
    # que acepta el flag --model de cada CLI (kimi usa prefijo kimi-code/ en la
    # plantilla headless).
    param([string]$Cli)
    switch ($Cli) {
        'claude' {
            @(
                [ordered]@{ id = 'fable';  capacidad = 10; costo = 3; contexto_k = 'desconocido' },
                # El alias 'opus' invoca Opus estandar (200K); la variante 1M es un alias aparte (opus[1m]).
                [ordered]@{ id = 'opus';   capacidad = 9;  costo = 3; contexto_k = 200 },
                [ordered]@{ id = 'sonnet'; capacidad = 7;  costo = 2; contexto_k = 200 },
                [ordered]@{ id = 'haiku';  capacidad = 5;  costo = 1; contexto_k = 200 }
            )
        }
        'codex' {
            @(
                [ordered]@{ id = 'gpt-5.6-sol';   capacidad = 9; costo = 3; contexto_k = 272 },
                [ordered]@{ id = 'gpt-5.6-terra'; capacidad = 7; costo = 2; contexto_k = 272 },
                [ordered]@{ id = 'gpt-5.6-luna';  capacidad = 5; costo = 1; contexto_k = 272 },
                [ordered]@{ id = 'gpt-5.5';       capacidad = 7; costo = 2; contexto_k = 272 }
            )
        }
        'kimi' {
            @(
                [ordered]@{ id = 'k3';                        capacidad = 8; costo = 2; contexto_k = 1024 },
                [ordered]@{ id = 'kimi-for-coding';           capacidad = 7; costo = 1; contexto_k = 256 },
                [ordered]@{ id = 'kimi-for-coding-highspeed'; capacidad = 6; costo = 1; contexto_k = 256 }
            )
        }
    }
}

function Get-CliDetection {
    # Sondeo local: instalado (Get-Command) y version (--version con tolerancia a fallos).
    param([string]$Cli)
    $result = [ordered]@{ instalado = $false; version = 'desconocido' }
    $cmd = Get-Command $Cli -ErrorAction SilentlyContinue
    if ($null -ne $cmd) {
        $result.instalado = $true
        try {
            $v = (& $Cli --version 2>&1 | Select-Object -First 1 | Out-String).Trim()
            if ($v) { $result.version = $v }
        } catch { }
    }
    $result
}

function Get-AuthStatus {
    # Best-effort sin gastar cuota: presencia de archivos de credenciales conocidos.
    # Con -Probe se hace una invocacion trivial real (consume una llamada minima).
    param([string]$Cli, [switch]$Probe)
    $credentialHints = @{
        'claude' = @("$env:USERPROFILE\.claude\.credentials.json", "$env:USERPROFILE\.claude.json")
        'codex'  = @("$env:USERPROFILE\.codex\auth.json")
        'kimi'   = @("$env:USERPROFILE\.kimi-code\credentials\kimi-code.json", "$env:USERPROFILE\.kimi\credentials.json")
    }
    foreach ($path in $credentialHints[$Cli]) {
        if (Test-Path $path) { return $true }
    }
    if ($Probe) {
        try {
            # Para la sonda se quita la seleccion de modelo (usa el default del CLI).
            $headless = (Get-DefaultHeadless $Cli) -replace '\s*--model\s+\S*\{modelo\}\S*', '' `
                -replace '\{prompt\}', 'responde solo: ok'
            $out = cmd /c "$headless 2>&1"
            if ($LASTEXITCODE -eq 0) { return $true } else { return $false }
        } catch { return $false }
    }
    'desconocido'
}

function Build-Inventory {
    # Construye la seccion clis a partir de detecciones (inyectables para tests).
    param(
        [hashtable]$Detections,   # cli -> @{instalado; version}
        [hashtable]$AuthStatus    # cli -> $true|$false|'desconocido'
    )
    $clis = [ordered]@{}
    foreach ($cli in $script:CliNames) {
        $det = $Detections[$cli]
        $entry = [ordered]@{
            instalado   = [bool]$det.instalado
            autenticado = $AuthStatus[$cli]
            version     = $det.version
            headless    = Get-DefaultHeadless $cli
            plan        = 'desconocido'
            cuota       = 'desconocido'
            modelos     = @(Get-SeedModels $cli)
        }
        $clis[$cli] = $entry
    }
    $clis
}

function Build-Asignacion {
    # Listas ordenadas por nivel: capacidad suficiente -> menor costo -> mayor capacidad.
    # Nunca excluye un CLI instalado (Constitucion IV). Nivel vacio -> mejores disponibles.
    param($Clis)
    $available = @()
    foreach ($cli in $Clis.Keys) {
        if (-not $Clis[$cli].instalado) { continue }
        foreach ($m in $Clis[$cli].modelos) {
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
            # Fallback por diseno: sin candidatos del nivel, los mejores disponibles.
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
      Regla (FR-004 / invariante 4): un valor del models.json existente que difiere de
      la propuesta previa (models.scan.json) fue editado por el usuario y PREVALECE.
      Sin propuesta previa, todo el existente se considera del usuario.
      Con -Force, gana la propuesta nueva siempre.
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
    # Sin scan previo el usuario es dueno de todo; editado a mano prevalece; sin editar entra lo nuevo.
    $exisJson = ConvertTo-Json -InputObject $Exis -Depth 10 -Compress
    $prevJson = if ($null -ne $Prev) { ConvertTo-Json -InputObject $Prev -Depth 10 -Compress } else { $null }
    # Asignacion directa (no via expresion if): el pipeline de PS enumeraria un array
    # de 1 elemento y lo reduciria a su elemento.
    if ($null -eq $prevJson -or $exisJson -ne $prevJson) { $winner = $Exis } else { $winner = $Prop }
    # La coma preserva arrays: cada frontera de funcion de PS desenrolla una vez.
    if ($winner -is [System.Collections.IList] -and $winner -isnot [string]) { return ,$winner }
    return $winner
}

function ConvertTo-JsonStringLiteral {
    param([string]$s)
    $escaped = $s -replace '\\', '\\' -replace '"', '\"' -replace "`r", '\r' -replace "`n", '\n' -replace "`t", '\t'
    '"' + $escaped + '"'
}

function ConvertTo-CanonicalJson {
    # Serializador propio: JSON deterministico con indentacion 2 (el ConvertTo-Json de
    # PS 5.1 usa un formato irregular que rompe el invariante 6 del contrato).
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
    # JSON canonico del proyecto: indentacion 2 espacios (contrato, invariante 6).
    param($Object)
    (ConvertTo-CanonicalJson $Object 0) + "`n"
}

function Write-Utf8NoBom {
    param([string]$Path, [string]$Content)
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $encoding)
}

function Invoke-ScanModels {
    param(
        [string]$RepoRoot,
        [switch]$Force,
        [switch]$ProbeAuth,
        [switch]$Json
    )
    if (-not $RepoRoot) {
        # scan-models.ps1 vive en <root>\.specify\scripts\powershell\ -> subir 3 niveles desde su carpeta.
        $scriptDir = Split-Path -Parent $PSCommandPath
        $RepoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $scriptDir))
    }
    $modelsPath = Join-Path $RepoRoot '.specify\models.json'
    $scanPath   = Join-Path $RepoRoot '.specify\models.scan.json'

    $detections = @{}
    $auth = @{}
    foreach ($cli in $script:CliNames) {
        $detections[$cli] = Get-CliDetection $cli
        $auth[$cli] = if ($detections[$cli].instalado) { Get-AuthStatus $cli -Probe:$ProbeAuth } else { $false }
    }

    $clis = Build-Inventory -Detections $detections -AuthStatus $auth
    $proposed = [ordered]@{
        clis       = $clis
        asignacion = Build-Asignacion $clis
    }

    $existing = $null
    $prevScan = $null
    if (Test-Path $modelsPath) {
        try { $existing = Get-Content $modelsPath -Raw | ConvertFrom-Json } catch {
            Write-Warning "models.json existente es invalido ($($_.Exception.Message)); se regenera desde cero."
        }
    }
    if (Test-Path $scanPath) {
        try { $prevScan = Get-Content $scanPath -Raw | ConvertFrom-Json } catch { }
    }

    $final = Merge-PreservingUserEdits -Proposed $proposed -Existing $existing -PrevScan $prevScan -Force:$Force

    # La propuesta cruda del scan se persiste SIEMPRE: es la referencia para detectar
    # ediciones manuales en la proxima ejecucion (invariante 4 del contrato).
    Write-Utf8NoBom -Path $scanPath   -Content (ConvertTo-Json2Space $proposed)
    Write-Utf8NoBom -Path $modelsPath -Content (ConvertTo-Json2Space $final)

    if ($Json) {
        $summary = [ordered]@{
            MODELS_JSON = $modelsPath
            SCAN_JSON   = $scanPath
            CLIS        = [ordered]@{}
        }
        foreach ($cli in $script:CliNames) {
            $summary.CLIS[$cli] = [ordered]@{
                instalado = $detections[$cli].instalado
                version   = $detections[$cli].version
                autenticado = $auth[$cli]
            }
        }
        $summary | ConvertTo-Json -Depth 5 -Compress
    } else {
        Write-Host "Inventario escrito en $modelsPath"
        foreach ($cli in $script:CliNames) {
            $st = if ($detections[$cli].instalado) { "instalado ($($detections[$cli].version))" } else { 'AUSENTE' }
            Write-Host ("  {0,-7} {1}" -f $cli, $st)
        }
        Write-Host "Revisa y corrige a mano: plan, cuota, capacidad/costo. Tus ediciones prevalecen."
    }
}

if ($MyInvocation.InvocationName -ne '.') {
    Invoke-ScanModels -RepoRoot $RepoRoot -Force:$Force -ProbeAuth:$ProbeAuth -Json:$Json
    # Los --version de CLIs externos pueden dejar LASTEXITCODE sucio; el scan fue exitoso.
    exit 0
}
