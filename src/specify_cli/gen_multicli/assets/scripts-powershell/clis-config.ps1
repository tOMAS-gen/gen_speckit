#Requires -Version 5.1
<#
.SYNOPSIS
  Administra definiciones genericas de CLI en .specify/models.json.
.NOTES
  Puede cargarse con dot-source para probar sus funciones sin ejecutar el punto de
  entrada. Las escrituras usan el serializador canonico del proyecto.
#>
[CmdletBinding()]
param(
    [ValidateSet('agregar', 'editar', 'eliminar', 'verificar')]
    [string]$Operacion,
    [string]$ModelsPath,
    [string]$Nombre,
    [string]$Headless,
    [object[]]$Modelos,
    [string[]]$PatronesCuota,
    [string]$VersionCmd,
    [switch]$Confirmado,
    [switch]$AprobarPrueba
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$script:ConfigScriptDir = Split-Path -Parent $PSCommandPath
. (Join-Path $script:ConfigScriptDir 'scan-models.ps1')
. (Join-Path $script:ConfigScriptDir 'platform.ps1')
. (Join-Path $script:ConfigScriptDir 'invoke-secondary.ps1')

function Read-CliInventory {
    param([string]$ModelsPath)
    if ([string]::IsNullOrWhiteSpace($ModelsPath)) { throw 'Falta -ModelsPath' }
    if (-not (Test-Path -LiteralPath $ModelsPath -PathType Leaf)) {
        throw "No existe el inventario: $ModelsPath"
    }
    # -Encoding UTF8 obligatorio: sin el, PS 5.1 lee ANSI y una re-escritura genera
    # mojibake en los acentos (bug real detectado en el campo plan).
    $data = ConvertTo-PlainValue (Get-Content -LiteralPath $ModelsPath -Raw -Encoding UTF8 | ConvertFrom-Json)
    if (-not ($data -is [System.Collections.IDictionary]) -or -not $data.Contains('clis')) {
        throw "Inventario invalido: falta la seccion 'clis'"
    }
    $data
}

function Get-CliValidationProblems {
    param(
        [string]$Nombre,
        [string]$Headless,
        [object[]]$Modelos,
        [string[]]$PatronesCuota,
        [System.Collections.IDictionary]$ExistingClis,
        [switch]$CheckDuplicate
    )
    $problems = New-Object System.Collections.Generic.List[string]
    if ([string]::IsNullOrWhiteSpace($Nombre) -or $Nombre -notmatch '^[a-z][a-z0-9-]*$') {
        $problems.Add('V1: formato de nombre invalido (kebab-case)')
    }
    if ($CheckDuplicate -and $null -ne $ExistingClis -and $ExistingClis.Contains($Nombre)) {
        $problems.Add('V2: duplicado: ofrecer editar el existente')
    }
    if ([string]::IsNullOrEmpty($Headless) -or -not $Headless.Contains('{prompt}')) {
        $problems.Add('V3: plantilla sin placeholder de prompt')
    }

    # Guardas anti-quirk PS 5.1: @() de un parametro tipado sin bindear produce un
    # valor cuyo .Count falla bajo StrictMode (repro minimo verificado).
    $modelList = @()
    if ($null -ne $Modelos) { $modelList = @($Modelos) }
    if ($modelList.Count -gt 1 -and
        ([string]::IsNullOrEmpty($Headless) -or
         (-not $Headless.Contains('{modelo}') -and $Headless -notmatch '(?i)(?:^|\s)--model(?:\s|=)'))) {
        $problems.Add('V4: no se puede seleccionar modelo')
    }
    if ($modelList.Count -lt 1) {
        $problems.Add('V5: modelo invalido (se requiere al menos uno)')
    } else {
        $ids = @{}
        for ($i = 0; $i -lt $modelList.Count; $i++) {
            $m = ConvertTo-PlainValue ($modelList[$i])
            $position = $i + 1
            if (-not ($m -is [System.Collections.IDictionary])) {
                $problems.Add("V5: modelo $position invalido (debe ser una tabla)")
                continue
            }
            $id = if ($m.Contains('id')) { [string]$m['id'] } else { '' }
            if ([string]::IsNullOrWhiteSpace($id)) {
                $problems.Add("V5: modelo $position invalido (id vacio)")
            } elseif ($ids.ContainsKey($id)) {
                $problems.Add("V5: modelo $position invalido (id duplicado '$id')")
            } else { $ids[$id] = $true }

            foreach ($field in @(@('capacidad', 1, 10), @('costo', 1, 3))) {
                $fieldName = [string]$field[0]
                $number = 0
                if (-not $m.Contains($fieldName) -or
                    -not [int]::TryParse([string]$m[$fieldName], [ref]$number) -or
                    $number -lt [int]$field[1] -or $number -gt [int]$field[2]) {
                    $problems.Add("V5: modelo $position invalido ($fieldName debe estar entre $($field[1]) y $($field[2]))")
                }
            }
        }
    }

    $patterns = @()
    if ($null -ne $PatronesCuota) { $patterns = @($PatronesCuota) }
    for ($i = 0; $i -lt $patterns.Count; $i++) {
        try { $null = New-Object System.Text.RegularExpressions.Regex([string]$patterns[$i]) }
        catch { $problems.Add("V6: patron $($i + 1) no es una regex valida") }
    }
    $problems.ToArray()
}

function Assert-CliDefinition {
    param(
        [string]$Nombre, [string]$Headless, [object[]]$Modelos,
        [string[]]$PatronesCuota, [System.Collections.IDictionary]$ExistingClis,
        [switch]$CheckDuplicate
    )
    $problems = @(Get-CliValidationProblems @PSBoundParameters)
    if ($problems.Count -gt 0) {
        throw ("Definicion rechazada:`n - " + ($problems -join "`n - "))
    }
}

function Get-CatalogData {
    param([string]$ModelsPath)
    $modelsDir = Split-Path -Parent ([System.IO.Path]::GetFullPath($ModelsPath))
    $catalogPath = Join-Path $modelsDir 'clis-catalog.json'
    if (-not (Test-Path -LiteralPath $catalogPath -PathType Leaf)) { return $null }
    ConvertTo-PlainValue (Get-Content -LiteralPath $catalogPath -Raw -Encoding UTF8 | ConvertFrom-Json)
}

function Get-AuthenticationStatus {
    param([string]$Nombre, $Catalog, [bool]$Installed)
    if (-not $Installed) { return $false }
    if ($null -eq $Catalog -or -not $Catalog.Contains('clis') -or
        -not $Catalog['clis'].Contains($Nombre)) { return 'desconocido' }
    $definition = $Catalog['clis'][$Nombre]
    if (-not $definition.Contains('auth_hints')) { return 'desconocido' }
    $os = Get-OsFamily
    if (-not $definition['auth_hints'].Contains($os)) { return 'desconocido' }
    foreach ($hint in @($definition['auth_hints'][$os])) {
        if (Test-Path -LiteralPath (Expand-PortablePath ([string]$hint))) { return $true }
    }
    $false
}

function Invoke-CliVerification {
    [CmdletBinding()]
    param(
        [string]$ModelsPath,
        [string]$Nombre,
        [switch]$AprobarPrueba,
        [int]$TimeoutSeconds = 120
    )
    $data = Read-CliInventory $ModelsPath
    if (-not $data['clis'].Contains($Nombre)) { throw "CLI '$Nombre' no existe en el inventario" }
    $catalog = Get-CatalogData $ModelsPath
    $diagnostics = New-Object System.Collections.Generic.List[object]

    # Nivel a: resolucion del ejecutable (inventario > catalogo > PATH generico).
    $exeHints = @(Get-CliDataValue -Inventory $data -Catalog $catalog -Cli $Nombre -Key 'exe_hints' -Default @())
    $exe = Resolve-Executable -Name $Nombre -ExeHints $exeHints
    $installed = $null -ne $exe
    if ($installed) {
        $diagnostics.Add([pscustomobject]@{
            nivel = 'a'; resultado = 'ok'; detalle = "ejecutable resuelto: $exe"; correccion = ''
        })
    } else {
        $diagnostics.Add([pscustomobject]@{
            nivel = 'a'; resultado = 'fallo'; detalle = 'no se resolvio el ejecutable'
            correccion = 'instalar el CLI o corregir el PATH'
        })
    }

    # Nivel b: autenticacion por hints detectables del SO actual.
    if (-not $installed) {
        $diagnostics.Add([pscustomobject]@{
            nivel = 'b'; resultado = 'omitido'; detalle = 'pendiente de nivel a'; correccion = 'resolver el nivel a primero'
        })
    } else {
        $auth = Get-AuthenticationStatus -Nombre $Nombre -Catalog $catalog -Installed $true
        if ($auth -eq $true) {
            $diagnostics.Add([pscustomobject]@{
                nivel = 'b'; resultado = 'ok'; detalle = 'autenticado'; correccion = ''
            })
        } elseif ($auth -eq $false) {
            $diagnostics.Add([pscustomobject]@{
                nivel = 'b'; resultado = 'fallo'; detalle = 'no autenticado'
                correccion = 'ejecutar el login del CLI'
            })
        } else {
            $diagnostics.Add([pscustomobject]@{
                nivel = 'b'; resultado = 'ok'; detalle = 'no verificable sin prueba'; correccion = ''
            })
        }
    }

    # Nivel c: invocacion de prueba real (opt-in).
    if (-not $installed) {
        $diagnostics.Add([pscustomobject]@{
            nivel = 'c'; resultado = 'omitido'; detalle = 'pendiente de nivel a'; correccion = 'resolver el nivel a primero'
        })
    } elseif (-not $AprobarPrueba) {
        $diagnostics.Add([pscustomobject]@{
            nivel = 'c'; resultado = 'omitido'; detalle = 'prueba real no solicitada'
            correccion = 'repetir con -AprobarPrueba (consume una llamada)'
        })
    } else {
        $entry = $data['clis'][$Nombre]
        $primerModelo = ''
        if ($entry.Contains('modelos') -and @($entry['modelos']).Count -gt 0) {
            $primerModelo = [string]$entry['modelos'][0]['id']
        }
        $prompt = 'responde solo: ok'
        $command = Get-HeadlessCommand -Inventory $data -Cli $Nombre -Model $primerModelo -Prompt $prompt
        $tmpBase = [System.IO.Path]::GetTempFileName()
        $outFile = "$tmpBase.out.log"
        $errFile = "$tmpBase.err.log"
        try {
            $start = Get-Date
            $r = Invoke-PortableProcess -Command $command -TimeoutSeconds $TimeoutSeconds `
                -OutFile $outFile -ErrFile $errFile
            $latency = [math]::Round(((Get-Date) - $start).TotalSeconds, 3)
            $texto = ''
            if (Test-Path -LiteralPath $outFile) { $texto += (Get-Content -LiteralPath $outFile -Raw) }
            if (Test-Path -LiteralPath $errFile) { $texto += "`n" + (Get-Content -LiteralPath $errFile -Raw) }
            $patterns = @(Get-QuotaPatternsFor -Inventory $data -Catalog $catalog -Cli $Nombre)
            $clasificacion = 'fallo'
            if (-not $r.timedOut -and $r.exitCode -eq 0) {
                $clasificacion = 'exito'
            } elseif (Test-QuotaPattern -Patterns $patterns -Text $texto) {
                $clasificacion = 'cuota'
            }
            $detalle = "comando: $command | clasificacion: $clasificacion | exit: $($r.exitCode) | latencia: ${latency}s"
            if ($clasificacion -eq 'exito') {
                $diagnostics.Add([pscustomobject]@{
                    nivel = 'c'; resultado = 'ok'; detalle = $detalle; correccion = ''
                })
            } elseif ($clasificacion -eq 'cuota') {
                $diagnostics.Add([pscustomobject]@{
                    nivel = 'c'; resultado = 'fallo'; detalle = $detalle
                    correccion = 'cuota agotada: esperar o revisar limites'
                })
            } else {
                $diagnostics.Add([pscustomobject]@{
                    nivel = 'c'; resultado = 'fallo'; detalle = $detalle
                    correccion = 'revisar plantilla o configuracion del CLI'
                })
            }
        } finally {
            Remove-Item -LiteralPath $tmpBase -ErrorAction SilentlyContinue
            Remove-Item -LiteralPath $outFile -ErrorAction SilentlyContinue
            Remove-Item -LiteralPath $errFile -ErrorAction SilentlyContinue
        }
    }

    # Actualiza SOLO los campos detectables (FR-008).
    $version = 'desconocido'
    if ($installed) {
        $versionCmd = [string](Get-CliDataValue -Inventory $data -Catalog $catalog -Cli $Nombre -Key 'version_cmd' -Default '--version')
        try {
            $args = @($versionCmd -split '\s+')
            $v = (& $exe @args 2>&1 | Select-Object -First 1 | Out-String).Trim()
            if ($v) { $version = $v }
        } catch { }
    }
    $authValue = if ($installed) { $auth } else { $false }
    $data['clis'][$Nombre]['instalado'] = $installed
    $data['clis'][$Nombre]['autenticado'] = $authValue
    $data['clis'][$Nombre]['version'] = $version
    Write-Utf8NoBom -Path $ModelsPath -Content (ConvertTo-Json2Space $data)

    ,@($diagnostics.ToArray())
}

function Update-CliAssignment {
    param($Data, [string]$ModelsPath)
    $enabled = [ordered]@{}
    foreach ($key in $Data['clis'].Keys) {
        $entry = $Data['clis'][$key]
        if ($entry.Contains('deshabilitado') -and [bool]$entry['deshabilitado']) { continue }
        $enabled[$key] = $entry
    }
    $proposed = Build-Asignacion $enabled

    # Semantica: la operacion explicita del usuario ES la nueva verdad del reparto,
    # pero un reordenamiento manual previo (existing != scan previo) debe sobrevivir.
    # Sin scan previo NO hay evidencia de ediciones manuales de asignacion: gana lo
    # regenerado (si no, un CLI nuevo jamas entraria al ranking).
    $scanPath = Join-Path (Split-Path -Parent ([System.IO.Path]::GetFullPath($ModelsPath))) 'models.scan.json'
    $previous = $null
    $scan = $null
    if (Test-Path -LiteralPath $scanPath -PathType Leaf) {
        try {
            $scan = ConvertTo-PlainValue (Get-Content -LiteralPath $scanPath -Raw | ConvertFrom-Json)
            if ($scan.Contains('asignacion')) { $previous = $scan['asignacion'] }
        } catch { }
    }
    if ($null -eq $previous) {
        $Data['asignacion'] = $proposed
    } else {
        $existing = $null
        if ($Data.Contains('asignacion')) { $existing = $Data['asignacion'] }
        $Data['asignacion'] = Merge-PreservingUserEdits -Proposed $proposed -Existing $existing -PrevScan $previous
    }
    # Actualizar la linea base del scan SOLO en su seccion asignacion, para que la
    # proxima operacion/escaneo compare contra el reparto posterior a esta operacion.
    if ($null -ne $scan) {
        $scan['asignacion'] = $proposed
        Write-Utf8NoBom -Path $scanPath -Content (ConvertTo-Json2Space $scan)
    }
}

function Save-CliInventory {
    param($Data, [string]$ModelsPath)
    Update-CliAssignment -Data $Data -ModelsPath $ModelsPath
    Write-Utf8NoBom -Path $ModelsPath -Content (ConvertTo-Json2Space $Data)
}

function Add-CliDefinition {
    [CmdletBinding()]
    param(
        [string]$ModelsPath, [string]$Nombre, [string]$Headless,
        [object[]]$Modelos, [string[]]$PatronesCuota, [string]$VersionCmd
    )
    $data = Read-CliInventory $ModelsPath
    $validation = @{
        Nombre = $Nombre; Headless = $Headless; Modelos = $Modelos
        PatronesCuota = $PatronesCuota; ExistingClis = $data['clis']; CheckDuplicate = $true
    }
    Assert-CliDefinition @validation

    $catalog = Get-CatalogData $ModelsPath
    $executable = Resolve-Executable -Name $Nombre
    $installed = $null -ne $executable
    $entry = [ordered]@{
        instalado = $installed
        autenticado = Get-AuthenticationStatus -Nombre $Nombre -Catalog $catalog -Installed $installed
        version = 'desconocido'
        headless = $Headless
        plan = 'desconocido'
        cuota = 'desconocido'
        origen = 'registrado'
        modelos = @($Modelos | ForEach-Object { ConvertTo-PlainValue $_ })
    }
    if ($PSBoundParameters.ContainsKey('PatronesCuota')) { $entry['patrones_cuota'] = @($PatronesCuota) }
    if ($PSBoundParameters.ContainsKey('VersionCmd')) { $entry['version_cmd'] = $VersionCmd }
    $data['clis'][$Nombre] = $entry
    Save-CliInventory -Data $data -ModelsPath $ModelsPath
    [pscustomobject]@{ operacion = 'agregar'; cli = $Nombre; instalado = $installed; autenticado = $entry['autenticado'] }
}

function Edit-CliDefinition {
    [CmdletBinding()]
    param(
        [string]$ModelsPath, [string]$Nombre, [string]$Headless,
        [object[]]$Modelos, [string[]]$PatronesCuota, [string]$VersionCmd
    )
    $data = Read-CliInventory $ModelsPath
    if (-not $data['clis'].Contains($Nombre)) { throw "CLI '$Nombre' no existe en el inventario" }
    $candidate = ConvertTo-PlainValue $data['clis'][$Nombre]
    foreach ($mapping in @(@('Headless', 'headless'), @('Modelos', 'modelos'),
                            @('PatronesCuota', 'patrones_cuota'), @('VersionCmd', 'version_cmd'))) {
        if ($PSBoundParameters.ContainsKey([string]$mapping[0])) {
            $candidate[[string]$mapping[1]] = ConvertTo-PlainValue ($PSBoundParameters[[string]$mapping[0]])
        }
    }
    $patterns = if ($candidate.Contains('patrones_cuota')) { @($candidate['patrones_cuota']) } else { @() }
    Assert-CliDefinition -Nombre $Nombre -Headless ([string]$candidate['headless']) `
        -Modelos @($candidate['modelos']) -PatronesCuota $patterns -ExistingClis $data['clis']
    $data['clis'][$Nombre] = $candidate
    Save-CliInventory -Data $data -ModelsPath $ModelsPath
    [pscustomobject]@{ operacion = 'editar'; cli = $Nombre }
}

function Get-ActiveCliTaskLabels {
    param([string]$ModelsPath, [string]$Nombre)
    $specsDir = Join-Path (Split-Path -Parent (Split-Path -Parent ([System.IO.Path]::GetFullPath($ModelsPath)))) 'specs'
    if (-not (Test-Path -LiteralPath $specsDir -PathType Container)) { return @() }
    $escaped = [regex]::Escape($Nombre)
    $warnings = @()
    foreach ($file in @(Get-ChildItem -LiteralPath $specsDir -Directory -ErrorAction SilentlyContinue |
            ForEach-Object { Join-Path $_.FullName 'tasks.md' } | Where-Object { Test-Path -LiteralPath $_ })) {
        $lineNumber = 0
        foreach ($line in @(Get-Content -LiteralPath $file)) {
            $lineNumber++
            if ($line -match '^\s*-\s*\[\s\]' -and $line -match "\[M:$escaped(?:/|\])") {
                $warnings += [pscustomobject]@{ archivo = $file; linea = $lineNumber; tarea = $line.Trim() }
            }
        }
    }
    $warnings
}

function Remove-CliDefinition {
    [CmdletBinding()]
    param([string]$ModelsPath, [string]$Nombre, [switch]$Confirmado)
    if (-not $Confirmado) { throw "Se requiere confirmacion explicita: repita con -Confirmado para dar de baja '$Nombre'" }
    $data = Read-CliInventory $ModelsPath
    if (-not $data['clis'].Contains($Nombre)) { throw "CLI '$Nombre' no existe en el inventario" }
    $warnings = @(Get-ActiveCliTaskLabels -ModelsPath $ModelsPath -Nombre $Nombre)
    $catalog = Get-CatalogData $ModelsPath
    $isCatalog = $null -ne $catalog -and $catalog.Contains('clis') -and $catalog['clis'].Contains($Nombre)
    if ($isCatalog) {
        $data['clis'][$Nombre]['deshabilitado'] = $true
        $change = 'deshabilitado'
    } else {
        $data['clis'].Remove($Nombre)
        $change = 'eliminado'
    }
    Save-CliInventory -Data $data -ModelsPath $ModelsPath
    [pscustomobject]@{ operacion = 'eliminar'; cli = $Nombre; cambio = $change; advertencias = $warnings }
}

if ($MyInvocation.InvocationName -ne '.') {
    foreach ($required in @('Operacion', 'ModelsPath', 'Nombre')) {
        if (-not (Get-Variable $required -ValueOnly)) { throw "Falta -$required" }
    }
    switch ($Operacion) {
        'agregar' {
            foreach ($required in @('Headless', 'Modelos')) {
                if (-not $PSBoundParameters.ContainsKey($required)) { throw "Falta -$required" }
            }
            $call = @{ ModelsPath = $ModelsPath; Nombre = $Nombre; Headless = $Headless; Modelos = $Modelos }
            if ($PSBoundParameters.ContainsKey('PatronesCuota')) { $call.PatronesCuota = $PatronesCuota }
            if ($PSBoundParameters.ContainsKey('VersionCmd')) { $call.VersionCmd = $VersionCmd }
            Add-CliDefinition @call
        }
        'editar' {
            $call = @{ ModelsPath = $ModelsPath; Nombre = $Nombre }
            foreach ($key in @('Headless', 'Modelos', 'PatronesCuota', 'VersionCmd')) {
                if ($PSBoundParameters.ContainsKey($key)) { $call[$key] = Get-Variable $key -ValueOnly }
            }
            Edit-CliDefinition @call
        }
        'eliminar' { Remove-CliDefinition -ModelsPath $ModelsPath -Nombre $Nombre -Confirmado:$Confirmado }
        'verificar' {
            Invoke-CliVerification -ModelsPath $ModelsPath -Nombre $Nombre -AprobarPrueba:$AprobarPrueba |
                Format-Table
        }
    }
}
